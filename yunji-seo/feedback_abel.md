# Yunji Seo

Email: yunjiseo@mit.edu  
GitHub username: yunji-seo  
Repository URL: https://github.com/onexi/ps06

You may find the project from a former 1.125 student useful. Note that this project is from 9 years ago. Today, of course, it would be completely different. But you might find his framing of the problem useful. 
https://www.youtube.com/watch?v=gLsWfUFTwz4
https://www.youtube.com/watch?v=Qjqk9_1u93o
https://www.youtube.com/watch?v=WpRWpHaHy8c
https://www.youtube.com/watch?v=5cR64X1tHZo



## Overall

BikeBalance is a well-bounded planning project with a clear decision, explicit constraints, and a small network. The worked three-station example makes the optimization understandable, and the distinction between balance and actual service improvement is appropriately careful.

## Could Be Stronger

There isn't a major proposal gap here. I'd make the planned tests more concrete by including a zero-movement budget, an already balanced network, unreachable targets, and a small case whose optimum can be checked by hand. Define the greedy comparator precisely so all three strategies use the same limits and objective order. It would also help to say how you'll resolve multiple equally good transfer plans. That makes your reproducibility target clearer: identical objective values and valid plans may matter more than selecting the exact same transfers every time.

## Distinctive Strength

You explicitly state that bike-kilometers are a distance measure and that better balance alone doesn't prove better service. That restraint strengthens the project. It gives the tool a clear purpose without claiming to solve demand forecasting, truck routing, or live operations, all of which you've sensibly left outside this version.
