# Design

Written before generating any picture, video or music. Updated after each user test.

## Brief

**Working title:** *When I Was Your Age*

**Logline.** A dad tells his kid how he got to school: miles of highland, the Blue Nile, a crumbling bridge, the Simien cliffs and the lava lake of Erta Ale. Each obstacle is wilder than the last, and when he finally arrives, the teacher says: "You're late again!"

**Audience.** Ethiopian friends my age (20s), who grew up hearing "when I was your age…" from their own parents. They understand Amharic. They watch on their phones, vertically, on Instagram, TikTok or Telegram.

**Intent.** At the end they should:
1. **Laugh in recognition.** "My dad says exactly this."
2. **Feel a little respect.** Under the exaggeration, many of our parents really did walk very far to school.

**Define statement.** How might we make Ethiopian friends my age laugh at the "when I was your age" story, and still leave them remembering that the walk was real?

**Constraints.**
- 60–90 s, in 9:16 and 16:9.
- Amharic narration with English subtitles.
- An original score ducked under the voice.
- An "made with AI" end card.
- Built in one day.

## Decisions

| Decision | Why |
|---|---|
| Dropped a dinosaur-extinction idea | It had no link to me or my family, and the brief asks for a story that matters to you and your family. |
| The narrator is **"a dad"**, an invented character, not my real father | A real person shown or voiced needs a recorded consent, or the film scores zero. An invented dad keeps the shared, recognisable story without depicting anyone real. The character must not be drawn to look like my father. |
| Cartoon style, not realistic camera shots | Exaggeration (lava, crocodiles) reads as a joke in a cartoon and as fake in realism. Image models also keep a simple cartoon character consistent more easily than a realistic face. |
| Real Ethiopian landmarks, each with a feature people recognise | The audience should think "I know that place". That pride is part of the respect beat. Each place escalates the danger. |
| The film ends on the teacher: "You're late again!" (not a "school was next door" punchline, not a confession from the dad) | After lava and cliffs, being scolded is the laugh. "Again" carries the respect: he did this journey every day, and it still wasn't enough. Ending at school, not back home, keeps the last beat sharp. |
| Subject in the centre of every frame | The 9:16 and 16:9 versions can be cut from the same images. |
| Text-free images; all words added in code | Image models garble text. Subtitles and the end card come from the storyboard. |

## Style

- **Look:** flat, hand-painted cartoon, warm colours, soft textured shading, simple shapes, bold outlines. It's like a children's picture book, not 3D and not anime.
- **Main character (young dad):** a boy of about 10, thin, short curly hair, a faded blue school shirt and khaki shorts, barefoot. He carries school books tied together with string.
- **Older dad (frame story):** the same character, about 45, a short beard with grey, in a home setting.
- **The kid (frame story):** a teenager on a sofa with a phone.
- **Motion:** slow and gentle, one movement per shot.

## Shot plan (draft v1, before user test 1)

Target: about 65 s including the end card.

| # | Shot | Place / feature | Length | Why this shot exists |
|---|---|---|---|---|
| 1 | The kid on the sofa complains that school is "so far" (a 10-minute walk). Dad leans in from the doorway. | A modern Addis apartment | 7 s | Sets up the moment every viewer knows, before the story starts. |
| 2 | Dawn. Young dad steps out of a round thatched hut (tukul) with his string-tied books. A rooster crows. | Highland village | 7 s | Who, where and when: the flashback begins. |
| 3 | Extreme wide shot. A tiny boy on an endless path through green highland hills and eucalyptus. | Ethiopian highlands | 7 s | Shows the distance, the first (true) part of the story. |
| 4 | He wades across a brown river, books held over his head. A crocodile watches. | Blue Nile | 8 s | First exaggeration. The danger begins. |
| 5 | In a dense green jungle, he tiptoes under the belly of a giant elephant. Colobus monkeys watch from the trees. | Chebera Churchura National Park, home of one of Ethiopia's largest elephant herds | 8 s | A real Ethiopian wilderness many viewers have only heard of. Elephants raise the danger after the crocodile. (Replaced the Portuguese Bridge on 2026-11-26, my choice.) |
| 6 | He climbs jagged green cliffs while gelada monkeys watch, unimpressed. | Simien Mountains | 8 s | Height. The geladas make it funny and recognisable. |
| 7 | He hops across black rocks over a glowing lava lake, his feet smoking. | Erta Ale, Afar | 8 s | The peak of the absurdity. |
| 8 | He arrives at a small schoolhouse, proud, his clothes soaked and dripping (from the Nile) while smoke rises from his hair (from Erta Ale). The stern teacher at the door, arms crossed: "You're late again!" | A rural school | 9 s | The ending. The laugh is the anticlimax. "Again" is the respect: this was every day. |
| 9 | End card: "Made with AI". | — | 3 s | Required, and honest about how it was made. |

The narration is the dad in the first person, written in English, translated to Amharic (GLM 5.3 Flash, see EXPERIMENTS.md E1), and voiced by Gemini TTS. The voice is a stock TTS voice, not a clone of anyone.

## User test 1: radio cut

Done on 2026-11-26. Four Ethiopian friends my age watched the cut with narration (Amharic voices, English subtitles, placeholder drone). Their overall reaction: **"this looks funny."**

| Person | What they said | What it told us |
|---|---|---|
| Mekdes | "That's so funny! Send it to me once you have the video." | The story works from the voice alone, before any picture exists, and she wants to see the film. |
| Paul | "Soo funny! Even the lava 😄" | The escalation lands, and the biggest exaggeration, walking over lava, gets the laugh. We kept Erta Ale as the last and most extreme obstacle before school. |
| Yonas | "You should post this somewhere!" | He would share it, which is the reaction the film is for. It is why the film is going public, as a LinkedIn post. |
| Yusuf | "Made me laugh so hard. You know, but it should say *znjerowochu yayugn neber* (ዝንጀሮዎቹ ያዩኝ ነበር, 'the monkeys used to watch me'), not *znjerowochu ayugn* (ዝንጀሮዎቹ አዩኝ, 'the monkeys watched me')." | **Changed the script.** The dad is describing a routine, so Amharic needs the past habitual, not a one-time past. The English moved to "would" / "used to", and `translation_notes` asks for the past habitual. Shot s06 now says `ዝም ብለው ያዩኝ ነበር` (see below). |

Mekdes, Paul and Yonas gave praise, which shows the comedy lands but not where it could be better. Yusuf's note was the one that changed the storyboard.

Changes made after this test:
- **From Yusuf:** the routine had to read as **every day, not one trip**. The English moved to "would" / "used to", and `translation_notes` asks for the past habitual. In English the difference is subtle; in Amharic it is clear, and it is what makes "You're late **again**" land.

From my own listening to the same cut, as the native speaker:
- The teacher's line was rewritten to `ዛሬም እንደገና አረፈድክ!` ("late *again* today!") for a sharper punchline.
- s05: the Portuguese Bridge was swapped for the Chebera Churchura jungle (elephants), a wilder escalation after the crocodile.
- Style: the generic picture-book look (style A) was replaced by doodle stick figures with a **kuncho** and a **gabi** (E5), so the characters read as Ethiopian, not generic.

Questions planned for the test:
- Where did you laugh?
- Did the ending land? What did you feel?
- Was anything confusing or too long?
- Would you send it to someone?

## User test 2: near-final cut

Done on 2026-11-26. I posted the finished 16:9 film in a Slack thread for my cohort, Ethiopian developers my age (the audience the film was made for), with one line: "a funny tribute to our parents who used to walk miles to reach school. Please take a look and tell me what you think." The thread got 13 replies within about 20 minutes, and the post got 27 🔥, 4 ❤️, 1 🙌 and 1 😆 reactions.

| Person | What they said | What it tells us |
|---|---|---|
| Henok Husen | "so cool" | Positive, no detail. |
| Tsion Habtesilassei | "So funny 😂. Great shots too" | The comedy lands, and the pictures hold up on their own. |
| Robel B. | "I loveee this! 😂 It turns out every parent has a similar story!" | The intent landed exactly: a shared story, laugh plus recognition. Two people reacted 😅 to this reply. |
| Haylemichael Tsega Gebrekidan | "he was a tourist not a student 🤣" | A new joke the viewer found himself: the "commute" tours Ethiopia's famous sights. The exaggeration reads as intended. |
| Tigrem Sahilu | "😄😃😀" | Positive, no detail. |
| Yabebal Fantaye | "This is great!" | Positive, no detail. |
| Eyosiyas Mengesha | "the exaggeration 😂👌" | Names the device that makes it work: the escalation from shot to shot. |

What changed because of it: **nothing in the storyboard.** Every reply was positive, nobody was confused, and the two specific comments (Robel, Eyosiyas) confirm the two things the film was built on: a story every parent tells, and escalation for the laugh. Haylemichael's "tourist" reading is a second joke we didn't plan, and it works for the film rather than against it.

What this test can't show: the replies are short and public, so people may hold back criticism in front of the group, and nobody said where they stopped watching. A next test would ask two or three people privately where they laughed and whether any shot felt long.
