# Jacqueline Pan

Email: jacqu311@mit.edu  
GitHub username: Jacquelineplj  
Repository URL: https://github.com/onexi/ps06

## Overall

TrueTrip makes the problem immediately understandable with the example where the more expensive room produces the cheaper trip. Keeping the comparison inside the traveler's existing search page is a thoughtful way to reduce the extra work you describe.

## Could Be Stronger

I'd start with one city and confirm the specific rating and routing sources before committing to US hotels in any city. The extension removes one dependency, but the other data sources still need a workable access and cost plan. I'd also make the cost example internally consistent: the second slide includes both parking and ride costs even though your formula says those apply to different travel modes. Show the selected mode and uncertainty range clearly, then test the final hotel ordering as well as each extracted fee.

## Distinctive Strength

Treating an unknown fee as unknown is an excellent design choice. It prevents missing information from making a hotel look artificially cheap. The proposed price-reversal cases are also a useful demonstration because they show whether the added information actually changes a decision.
