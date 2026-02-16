"""CQS Test Harness — V2 Equal-Tool Design.

Generates responses for all three conditions with equal tool access.
Single variable under test: methodology support form.

Usage:
    # Run all three conditions sequentially (recommended)
    python -m src.eval.harness --condition all --rag-index-dir results/rag_ablation/index

    # Run single condition
    python -m src.eval.harness --condition control
    python -m src.eval.harness --condition rag --rag-index-dir results/rag_ablation/index
    python -m src.eval.harness --condition pragmatics

Output: results/v2_redo/stage1/{condition}_responses_{timestamp}.jsonl
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

from .agent_loop import AgentLoop, PRAGMATICS_ONLY_TOOL
from .mcp_client import MCPClient
from .models import ResponseRecord
from .rag_retriever import RAGRetriever


class CQSTestHarness:
    """Main test runner for CQS V2 evaluation."""

    def __init__(
        self,
        battery_path: str = "src/eval/battery/queries.yaml",
        output_dir: Optional[str] = None,
        project_root: str = "/Users/brock/Documents/GitHub/census-mcp-server",
        condition: str = "all",
        rag_index_dir: Optional[str] = None,
    ):
        self.project_root = Path(project_root)
        self.battery_path = self.project_root / battery_path
        self.condition = condition

        # V2 output directory
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_dir is None:
            output_dir = "results/v2_redo/stage1"
        self.output_dir = self.project_root / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load battery
        with open(self.battery_path) as f:
            battery = yaml.safe_load(f)
            self.queries = battery["queries"]

        # Load eval config
        config_path = self.project_root / "src/eval/judge_config.yaml"
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # MCP client
        self.mcp_client = MCPClient(project_root=str(self.project_root))
        self.agent_loop = None

        # RAG retriever (lazy init)
        self.rag_index_dir = rag_index_dir or "results/rag_ablation/index"
        self.rag_retriever = None

        # Stats
        self.completed = {"control": [], "rag": [], "pragmatics": []}
        self.failed = {"control": [], "rag": [], "pragmatics": []}

    def _output_path(self, cond: str) -> Path:
        """Generate output path for a condition."""
        return self.output_dir / f"{cond}_responses_{self.timestamp}.jsonl"

    def _get_completed_ids(self, path: Path) -> set[str]:
        """Read output file to get already-completed query IDs for resume."""
        if not path.exists():
            return set()
        completed = set()
        with open(path) as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        completed.add(record["query_id"])
                    except json.JSONDecodeError:
                        continue
        return completed

    async def _run_condition(
        self,
        cond: str,
        queries_to_run: list[dict],
        output_path: Path,
    ) -> None:
        """Run a single condition across all queries."""
        # Check for resume
        completed_ids = self._get_completed_ids(output_path)
        remaining = [q for q in queries_to_run if q["id"] not in completed_ids]

        if completed_ids:
            print(f"  Resume: skipping {len(completed_ids)} completed, {len(remaining)} remaining")

        if not remaining:
            print(f"  All queries already complete for {cond}")
            return

        for i, query in enumerate(remaining, 1):
            query_id = query["id"]
            query_text = query["text"]
            print(f"  [{i}/{len(remaining)}] {query_id}: {query_text[:55]}...")

            try:
                start = time.time()

                if cond == "control":
                    record = await self.agent_loop.run_control(query_text, query_id)
                elif cond == "rag":
                    if self.rag_retriever is None:
                        self.rag_retriever = RAGRetriever(
                            str(self.project_root / self.rag_index_dir)
                        )
                    record = await self.agent_loop.run_rag(query_text, query_id, self.rag_retriever)
                elif cond == "pragmatics":
                    record = await self.agent_loop.run_pragmatics(query_text, query_id)
                else:
                    raise ValueError(f"Unknown condition: {cond}")

                elapsed = time.time() - start

                # Contamination check: verify no pragmatics tool calls in control/rag
                if cond in ("control", "rag"):
                    pragma_calls = [tc for tc in record.tool_calls
                                    if tc.tool_name == PRAGMATICS_ONLY_TOOL]
                    if pragma_calls:
                        raise RuntimeError(
                            f"CONTAMINATION DETECTED: {cond} condition made "
                            f"{len(pragma_calls)} calls to {PRAGMATICS_ONLY_TOOL}!"
                        )

                # Write incrementally
                with open(output_path, "a") as f:
                    f.write(record.model_dump_json() + "\n")

                # Log summary
                n_tools = len(record.tool_calls)
                chars = len(record.response_text)
                extra = ""
                if cond == "rag" and record.retrieved_chunks:
                    extra = f", {len(record.retrieved_chunks)} chunks"
                if cond == "pragmatics":
                    extra = f", {len(record.pragmatics_returned)} pragmatics"
                print(f"    ✓ {elapsed:.1f}s, {chars} chars, {n_tools} tool calls{extra}")

                self.completed[cond].append(query_id)

            except Exception as e:
                print(f"    ✗ ERROR: {e}")
                self.failed[cond].append((query_id, str(e)))

    async def run(self, query_ids: Optional[list[str]] = None) -> None:
        """Run evaluation for specified conditions."""
        print("=" * 60)
        print("CQS Test Harness — V2 Equal-Tool Design")
        print(f"Timestamp: {self.timestamp}")
        print("=" * 60)

        # Determine which conditions to run
        if self.condition == "all":
            conditions = ["control", "rag", "pragmatics"]
        else:
            conditions = [self.condition]

        print(f"Conditions: {conditions}")
        print(f"Output dir: {self.output_dir}")
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
            print("ERROR: MCP health check failed.")
            await self.mcp_client.stop()
            return

        # List available tools for verification
        all_tools = await self.mcp_client.list_tools()
        tool_names = [t["name"] for t in all_tools]
        print(f"✓ MCP server healthy — tools: {tool_names}")
        print()

        # Initialize agent loop
        caller_config = self.config.get("caller", {})
        self.agent_loop = AgentLoop(
            self.mcp_client,
            model=caller_config.get("model", "claude-sonnet-4-5-20250929"),
            max_tokens=caller_config.get("max_tokens", 2048),
            max_tool_rounds=caller_config.get("max_tool_rounds", 20),
        )

        # Filter queries
        queries = self.queries
        if query_ids:
            queries = [q for q in self.queries if q["id"] in query_ids]
            print(f"Running {len(queries)} selected queries")
        else:
            print(f"Running all {len(queries)} queries")
        print()

        # Run each condition
        start_time = time.time()
        for cond in conditions:
            output_path = self._output_path(cond)
            print(f"--- {cond.upper()} ({len(queries)} queries) → {output_path.name} ---")
            await self._run_condition(cond, queries, output_path)
            print()

        # Stop MCP
        print("Stopping MCP server...")
        await self.mcp_client.stop()

        # Summary
        total_time = time.time() - start_time
        print()
        print("=" * 60)
        print("V2 Stage 1 Summary")
        print("=" * 60)
        for cond in conditions:
            n_ok = len(self.completed[cond])
            n_fail = len(self.failed[cond])
            path = self._output_path(cond)
            print(f"  {cond:12s}: {n_ok} completed, {n_fail} failed → {path.name}")
        print(f"  Total time: {total_time:.1f}s")

        if any(self.failed[c] for c in conditions):
            print()
            print("Failed queries:")
            for cond in conditions:
                for qid, error in self.failed[cond]:
                    print(f"  [{cond}] {qid}: {error}")

        # Contamination summary
        print()
        print("Contamination check:")
        for cond in conditions:
            path = self._output_path(cond)
            if path.exists():
                pragma_count = 0
                total_records = 0
                with open(path) as f:
                    for line in f:
                        if line.strip():
                            rec = json.loads(line)
                            total_records += 1
                            for tc in rec.get("tool_calls", []):
                                if tc["tool_name"] == PRAGMATICS_ONLY_TOOL:
                                    pragma_count += 1
                if cond == "pragmatics":
                    status = f"✓ {pragma_count} calls (expected)"
                elif pragma_count == 0:
                    status = "✓ CLEAN"
                else:
                    status = "✗ CONTAMINATED"
                print(f"  {cond:12s}: {pragma_count} {PRAGMATICS_ONLY_TOOL} calls across {total_records} records — {status}")

        print("=" * 60)


async def main_async():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="CQS V2 Test Harness — Equal-Tool Design")
    parser.add_argument(
        "--query-ids",
        nargs="+",
        help="Specific query IDs to run (e.g., NORM-001 GEO-006)",
    )
    parser.add_argument(
        "--condition",
        choices=["control", "pragmatics", "rag", "all"],
        default="all",
        help="Which condition(s) to run (default: all)",
    )
    parser.add_argument(
        "--rag-index-dir",
        default="results/rag_ablation/index",
        help="Path to RAG index directory (default: results/rag_ablation/index)",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (default: results/v2_redo/stage1)",
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

    harness = CQSTestHarness(
        output_dir=args.output_dir,
        project_root=str(project_root),
        condition=args.condition,
        rag_index_dir=args.rag_index_dir,
    )

    await harness.run(query_ids=args.query_ids)


def main():
    """Synchronous entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
