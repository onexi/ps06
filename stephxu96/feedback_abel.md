# Steph Xu

Email: stephxu@mit.edu  
GitHub username: stephxu96  
Repository URL: https://github.com/onexi/ps06

Great focus! At the same time make sure you push on the feasibility in the early part of the project. 

## Overall

PruneAgent has a clear experimental structure, with baselines built before the agent and an explicit order for reducing scope. I liked the focus on a constrained run that can stop and return its last accepted plan rather than treating every compression target as achievable.

## Could Be Stronger

I'd define equal size in terms of the artifact and memory measurement you will actually report, including how pruned and quantized weights are stored and loaded. That connects the evaluation to the memory problem motivating the project. Also clarify whether the 15% perplexity limit is measured against the original model or only the previous step. A sequence of individually acceptable steps could have a very different cumulative effect. Keep a final quality check separate from the measurements used to choose actions, and make a well-supported negative result an acceptable research outcome.

I would significantly narrow the scope. Consider:

1. Take a small Qwen model.
2. Use an existing pruning implementation.
3. Build a simple agent that selects layer-specific pruning levels.
4. Compare its results with conventional pruning at the same model size.

I would eliminate quantization from the initial scope.

The key question is not whether an AI agent can prune a model. We already have tools that do that. It's whether an AI agent can make better pruning decisions than an existing algorithm.

## Distinctive Strength

Checkpointing and exact rollback are valuable parts of this design, especially with an interruptible compute environment. They make it possible to inspect which changes were accepted and repeat the comparison. That attention to the experimental workflow should help you produce a useful result even if the agent doesn't outperform the strongest baseline.
