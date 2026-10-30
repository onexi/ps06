# Ghaida Aljuhani

Email: aljuhaga@mit.edu  
GitHub username: Ghaida486  
Repository URL: https://github.com/onexi/ps06

## Overall

HomePulse connects a clear household question to a concrete dataset and a manageable application. I liked the separation between model development and the user-facing prediction flow, especially saving the fitted preprocessing with the model so the two stay together.

## Could Be Stronger

I'd make the evaluation more specific before training: name the baseline, the error measure, and what improvement would make the estimate useful. Show errors for different home types or regions as well as the overall result. Also clarify how the survey will support the comparisons you show, including how you'll handle its weights and the limits of using 2020 records for a present-day estimate. A short explanation of uncertainty would help someone understand how much confidence to place in a predicted annual kWh value.

## Distinctive Strength

Your plan to evaluate on untouched test households gives the project a credible way to check whether the prediction generalizes. Combined with the readable architecture diagram, it makes this feel like a focused modeling project with a useful interface, rather than a dashboard built around an unexplained number.
