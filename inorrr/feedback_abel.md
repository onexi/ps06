# Yinuo Zhao

Email: yinuozha@mit.edu  
GitHub username: inorrr  
Repository URL: https://github.com/onexi/ps06

Legal support is tremendously important. In fact there are a number of companies out in the market doing precisely this. One of the most famous ones is Harvey. It's perfectly fine to replicate some of what they do, especially if it gives you understanding of the problem. However you might want to take a look at what they do just for inspiration or perhaps focus tighter on some aspect that you might feel is not addressed or that you would like to understand at a deeper level.  

## Overall

Your proposal makes a clear distinction between finding cases and helping someone inspect their relevance. The persistent collection, source passages, and separate feedback loop form a coherent workspace, with a research question that can be tested on a bounded corpus.

## Could Be Stronger

I'd choose the first topic and court subset early and turn the relevance criteria into a short reviewer guide. The proposal already recognizes the need for legal expertise; securing that reviewer is an important dependency for the comparison. Include the reviewer's time and feedback effort when comparing the three conditions, not just retrieval calls and model cost. Otherwise the feedback condition could look more efficient while relying on substantial extra human work. Keep later evaluation judgments separate from the examples used to steer the search, as you propose.

## Distinctive Strength

Treating an unfavorable case as potentially relevant is a particularly good choice. It keeps the system from learning that useful means supportive of the user's preferred argument. Separating saving from voting also lets someone keep an important contrary case without confusing the feedback signal.
