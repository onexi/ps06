# Mingxi Wang

Email: harrris@mit.edu  
GitHub username: harrrisw  
Repository URL: https://github.com/onexi/ps06

Great project. One of the first thoughts that came to mind was, "How do you understand your user?" The example you give of live music, it's a great one. However what about those that would prefer, say, a poetry reading? And how do you get to know the user? Perhaps one way is to leverage the LLM data about the user. LLMs know a tremendous amount about a person.  

## Overall

Offhours gives the user a concrete, understandable experience, and the comparison between an LLM and an LLM with a solver is a useful project question. The three-stop limit and recorded API data provide a practical starting point for a controlled evaluation.

## Could Be Stronger

I'd check that the solver preserves required activities as well as timing and budget. Your example marks live music as a must, but one of the candidate plans is comedy followed by dessert. That is a useful test case for distinguishing hard requirements from preferences. I'd also make Boston the demonstrated scope and treat other cities as unvalidated coverage until tested. Across the 60 requests, report infeasible requests separately so the system can honestly return no plan rather than relaxing something the user required.

## Distinctive Strength

The calendar tests go beyond a successful write to include confirmation and duplicate events under API failures. That is a thoughtful detail for an assistant that acts on the user's behalf: a useful recommendation can still become a frustrating experience if a retry creates multiple events.
