"""CQS Test Harness - Main test runner for Phase 4B evaluation.

Generates paired control/treatment responses for CQS judge scoring.
"""
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from .agent_loop import AgentLoop
from .mcp_client import MCPClient
from .models import QueryPair


class CQSTestHarness:
    """Main test runner for CQS evaluation."""

    def __init__(
        self,
        battery_path: str = "src/eval/battery/queries.yaml",
        output_path: Optional[str] = None,
        project_root: str = "/Users/brock/Documents/GitHub/census-mcp-server",
    ):
        """Initialize harness.

        Args:
            battery_path: Path to queries YAML file
            output_path: Path to output JSONL file (auto-generated if None)
            project_root: Project root directory
        """
        self.project_root = Path(project_root)
        self.battery_path = self.project_root / battery_path

        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"results/cqs_responses_{timestamp}.jsonl"
        self.output_path = self.project_root / output_path

        # Ensure results directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load battery
        with open(self.battery_path) as f:
            battery = yaml.safe_load(f)
            self.queries = battery["queries"]

        # Initialize clients (will be started in run())
        self.mcp_client = MCPClient(project_root=str(self.project_root))
        self.agent_loop = None

        # Stats
        self.completed_queries = []
        self.failed_queries = []

    def _get_completed_query_ids(self) -> set[str]:
        """Read output file to get already-completed query IDs for resume.

        Returns:
            Set of query IDs that have been completed
        """
        if not self.output_path.exists():
            return set()

        completed = set()
        with open(self.output_path) as f:
            for line in f:
                if line.strip():
                    try:
                        pair = json.loads(line)
                        completed.add(pair["query_id"])
                    except json.JSONDecodeError:
                        continue

        return completed

    async def run(self, query_ids: Optional[list[str]] = None) -> None:
        """Run full battery or subset. Writes JSONL incrementally.

        Args:
            query_ids: If provided, only run these query IDs. Otherwise run all.
        """
        print("=" * 60)
        print("CQS Test Harness - Phase 4B Evaluation")
        print("=" * 60)
        print()

        # Start MCP server
        print("Starting MCP server...")
        try:
            await self.mcp_client.start()
        except Exception as e:
            print(f"ERROR: Failed to start MCP server: {e}")
            return

        # Health check
        print("Running health check...")
        if not await self.mcp_client.health_check():
            print("ERROR: MCP health check failed. Expected tools not available.")
            await self.mcp_client.stop()
            return
        print("✓ MCP server healthy")
        print()

        # Initialize agent loop
        self.agent_loop = AgentLoop(self.mcp_client)

        # Filter queries if specific IDs requested
        queries_to_run = self.queries
        if query_ids:
            queries_to_run = [q for q in self.queries if q["id"] in query_ids]
            print(f"Running {len(queries_to_run)} selected queries: {query_ids}")
        else:
            print(f"Running all {len(queries_to_run)} queries")

        # Check for resume
        completed_ids = self._get_completed_query_ids()
        if completed_ids:
            print(f"Resume mode: Skipping {len(completed_ids)} already-completed queries")
            queries_to_run = [q for q in queries_to_run if q["id"] not in completed_ids]

        print(f"Queries remaining: {len(queries_to_run)}")
        print()

        # Run queries
        start_time = time.time()

        for i, query in enumerate(queries_to_run, 1):
            query_id = query["id"]
            query_text = query["text"]

            print(f"[{i}/{len(queries_to_run)}] {query_id}: {query_text[:60]}...")

            try:
                # Run control
                print("  Running CONTROL...")
                control_start = time.time()
                control_response = await self.agent_loop.run_control(query_text, query_id)
                control_time = time.time() - control_start
                print(f"  ✓ Control complete ({control_time:.1f}s, {len(control_response.response_text)} chars)")

                # Run treatment
                print("  Running TREATMENT...")
                treatment_start = time.time()
                treatment_response = await self.agent_loop.run_treatment(query_text, query_id)
                treatment_time = time.time() - treatment_start
                print(
                    f"  ✓ Treatment complete ({treatment_time:.1f}s, {len(treatment_response.response_text)} chars, "
                    f"{len(treatment_response.tool_calls)} tool calls, "
                    f"{len(treatment_response.pragmatics_returned)} pragmatics)"
                )

                # Create query pair
                pair = QueryPair(
                    query_id=query_id,
                    query_text=query_text,
                    category=query["category"],
                    difficulty=query["difficulty"],
                    control=control_response,
                    treatment=treatment_response,
                )

                # Write to JSONL immediately (incremental checkpointing)
                with open(self.output_path, "a") as f:
                    f.write(pair.model_dump_json() + "\n")

                self.completed_queries.append(query_id)
                print(f"  ✓ Saved to {self.output_path}")
                print()

            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                self.failed_queries.append((query_id, str(e)))
                print()
                # Continue to next query, don't abort

        # Stop MCP server
        print("Stopping MCP server...")
        await self.mcp_client.stop()

        # Summary
        total_time = time.time() - start_time
        print()
        print("=" * 60)
        print("Run Summary")
        print("=" * 60)
        print(f"Completed: {len(self.completed_queries)}")
        print(f"Failed: {len(self.failed_queries)}")
        print(f"Total time: {total_time:.1f}s")
        print(f"Output: {self.output_path}")

        if self.failed_queries:
            print()
            print("Failed queries:")
            for qid, error in self.failed_queries:
                print(f"  {qid}: {error}")

        print("=" * 60)


async def main_async():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="CQS Test Harness - Generate paired responses")
    parser.add_argument(
        "--query-ids",
        nargs="+",
        help="Specific query IDs to run (e.g., NORM-001 GEO-006). If not provided, runs all.",
    )
    parser.add_argument(
        "--output",
        help="Output JSONL path (default: results/cqs_responses_TIMESTAMP.jsonl)",
    )
    args = parser.parse_args()

    # Load .env
    project_root = Path(__file__).parent.parent.parent
    load_dotenv(project_root / ".env")

    # Verify API keys
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not found in environment")
        sys.exit(1)
    if not os.environ.get("CENSUS_API_KEY"):
        print("ERROR: CENSUS_API_KEY not found in environment")
        sys.exit(1)

    # Run harness
    harness = CQSTestHarness(
        output_path=args.output,
        project_root=str(project_root),
    )

    await harness.run(query_ids=args.query_ids)


def main():
    """Synchronous entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
