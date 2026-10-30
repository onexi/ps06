# Omar Contreras Cabanillas

Email: omarcc96@mit.edu  
GitHub username: omarcontreras96  
Repository URL: https://github.com/onexi/ps06

I was just thinking about your proposal after watching the latest Claude release.
https://www.youtube.com/watch?v=yMnFHFf43Qg

When I think about the general audience and their ability to use these increasingly powerful capabilities effectively, I see a real challenge.

As AI reaches broader audiences, I think we'll need to develop new abstractions and interaction models that make its capabilities more accessible and intuitive.

I think your proposal fits very well into this picture.

## Overall

Do That There has a distinctive interaction idea, and the proposal explains how word timing, selection, and pointer history could make short commands meaningful. The choice to limit the first version to three apps and reduce command count before dropping verification is sensible.

## Could Be Stronger

I'd tighten the match between the audience and the input method. Holding a key and pointing may still be difficult for some people you describe, so identify the first user group that can use those controls and test the interaction with them. I'd also separate the attention-signal experiment from the claim of fewer words than existing voice control. Your built-in baseline can test the value of those signals, but it doesn't automatically represent an incumbent product. Use comparable tasks and measure completed actions, correction effort, and mistaken targets alongside word count.

## Distinctive Strength

Verifying the resulting application state is a strong design choice. A tool call returning successfully isn't enough to show that the intended file moved or the intended message changed. Your proposal makes that distinction part of the interaction, where the user actually experiences success or failure.
