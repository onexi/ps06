# Tianyu Zhao

Email: tzhao1@hsph.harvard.edu  
GitHub username: zhaotianyu0702  
Repository URL: https://github.com/onexi/ps06

Great data management and visualization problem. Try to identify your risks early on to make sure that you keep the project in scope.  

## Overall

Travel Atlas communicates the proposed experience clearly through the atlas and recap mockups. The path from photo metadata to AI suggestions, user review, and a saved record is easy to follow, and the evaluation includes the correction time that could otherwise hide extra work.

## Could Be Stronger

I'd add an explicit scope-and-risk decision. Four AI functions, accounts, a map, and three export formats are a substantial first version; choose the smallest complete import-to-recap flow and make short video optional if necessary. Also define how you'll handle private photos and location data, including what leaves the device for the multimodal API and what becomes visible in a shared recap. For the masked-GPS tests, include ordinary scenes with no reliable location clues so the system can leave a place unresolved rather than always proposing a city.

## Distinctive Strength

Keeping metadata and inferred places visibly separate is a thoughtful design choice. A plausible location guess shouldn't silently become part of someone's travel history. The confirm, edit, and reject steps give the user a way to preserve that distinction before the information spreads into maps and exported recaps.
