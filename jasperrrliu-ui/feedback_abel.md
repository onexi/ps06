# Jasper (Yuetong) Liu

Email: jasperli@mit.edu  
GitHub username: jasperrrliu-ui  
Repository URL: https://github.com/onexi/ps06

You mean find the following write-up by Anthropic on workflows useful as you consider the scenarios in customer service:
https://www.anthropic.com/research/building-effective-agents 

## Overall

Your retail agent proposal focuses on a useful question: whether the agent knows when to ask, inspect a record, or act. Three request families and simulated company data give you a manageable setting for studying those decisions.

## Could Be Stronger

I'd make a few complete conversations part of the core evaluation. The scope slide makes them optional, while the final slide promises all three request families end to end. Resolving that mismatch will make the deliverable clearer. For the checkpoint labels, define acceptable alternative actions and check a sample where the labeling models agree, as well as where they disagree. Agreement alone doesn't show that the policy interpretation is right. Keep checkpoints from the same conversation together when splitting development and test data so the final check uses genuinely separate examples.

## Distinctive Strength

You explicitly recognize that the original representative's action isn't automatically the correct answer. That is a strong foundation for an evaluation project. Reviewing the labels against policy gives the benchmark a defensible meaning and makes failure analysis more useful than simply counting differences from a transcript.
