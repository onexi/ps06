# Zhekai Li

Email: zhekaili@mit.edu  
GitHub username: Zhekai-Li  
Repository URL: https://github.com/onexi/ps06

I really enjoyed your presentation today.

## Overall

TS-Cov frames a focused research question: when does selecting context help a forecaster, and at what cost? The proposal makes room for a meaningful negative result, with reproducible code and comparisons as the deliverable.

## Could Be Stronger

I'd make the budgeted selection strategy more concrete. Show what the agent can observe when it chooses a bundle, which feedback it receives, and how those choices are kept separate from the final test windows. Also explain how the same candidate information becomes numerical covariates for one forecaster and text for the other. Without that detail, a performance difference could come from the representation or the forecaster rather than context selection. A small worked example from the proposed commodity or currency data would connect the opening illustration to the actual experiment.

## Distinctive Strength

Your explicit attention to timestamps and model vintage is a strong part of the design. Context selection is only useful if the information could have been available when the forecast was made. Treating that as part of the protocol makes the eventual conclusion much more credible.
