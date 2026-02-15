# Deep Agentic Thoughts: The Illusion of Control

## (Stack Handley Comedy Draft — write later, post-FCSM)

### The Premise

Claude Code skills are just prompt libraries with better packaging. The entire ecosystem 
is publishing "here's my cool skill" with:
- Zero testbench
- Zero benchmark
- Zero evidence it outperforms the null skill (just letting the model do its thing)
- Zero replication

And everyone's over-engineering them — 47-step instructions, rigid formatting rules, 
elaborate guardrails — creating the **illusion of control** over a stochastic process.

Shhh... there is no leash.

### The Bit

The more detailed and rigid your skill instructions, the more brittle the system becomes.
You're not training a dog. You're writing a horoscope for a dice roll and then claiming 
credit when it lands on 6.

"My skill says to ALWAYS use structured output with XML tags and NEVER deviate from 
the 14-step reasoning chain..." → model ignores half of it, produces good output anyway 
because it's a frontier model, author claims the skill worked.

**Survivorship bias for prompts.** You only see the skills people publish. You don't see 
the 400 iterations that didn't work, or the fact that the "working" version works because 
the model is good, not because the skill is good.

### The Actual Problem

No one is asking: **compared to what?**

- Does your skill outperform no skill? (Measure it.)
- Does your skill outperform a one-sentence instruction? (Measure it.)
- Does your skill work across models? (Test it.)
- Does your skill work next month when the model updates? (It won't.)

This is pre-evidence-based medicine. Practitioners sharing anecdotes: "I gave my patient 
this tincture and they got better!" Cool. Was there a control group? Did you measure 
the effect size? Or did the patient just... get better because immune systems exist?

### The Parallel to RAG

Same energy as the RAG technique zoo:
- "Use HyPE!" (compared to what? on what task? measured how?)
- "My GraphRAG pipeline gets amazing results!" (versus vanilla RAG? versus just asking the model?)
- "This reranking strategy improved relevance!" (by how much? on whose benchmark?)

Everyone's optimizing the plumbing. Nobody's testing the water.

### The Uncomfortable Truth

The models are getting better faster than the skill authors can iterate. Your carefully 
crafted 2000-token skill instruction that compensates for GPT-4's weaknesses is technical 
debt the moment GPT-5 drops. You're building compensatory complexity (the Jobs Doctrine 
problem) instead of encoding durable knowledge.

What survives model upgrades:
- Domain knowledge (what to know)
- Quality requirements (what good looks like)
- Evaluation frameworks (how to measure)

What doesn't survive:
- Formatting hacks
- Reasoning chain templates  
- Output structure enforcement
- Token optimization tricks
- "Always do X before Y" procedural scripts

### The Punchline

The best Claude Code skill is a good CLAUDE.md that encodes your project's actual 
conventions — verified against your actual codebase, evolved through actual use. 

Not a marketplace download from someone who solved a different problem with a 
different codebase on a different model version three months ago.

The second best skill is no skill at all, because the model probably already knows 
how to do the thing, and your 47-step instruction set is just adding noise to the 
signal.

### The COOS Connection (serious note)

This is literally what COOS proves empirically. We ran the experiment:
- Control: let the model do its thing
- Treatment: give it curated expert judgment
- Measured the effect size with a real rubric

d = 1.92 on uncertainty communication. That's not a vibe. That's a number.

Now imagine if every "awesome Claude Code skill" had to show its Cohen's d before 
getting published. The marketplace would be a lot smaller. And a lot more useful.

### Title Options
- "The Illusion of Control: Why Your Claude Code Skill Is a Horoscope"
- "Shhh... There Is No Leash"  
- "Pre-Evidence-Based Prompt Engineering"
- "Everyone's Optimizing the Plumbing, Nobody's Testing the Water"
- "Your Skill Doesn't Work, Your Model Is Just Good"
