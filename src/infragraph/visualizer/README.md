# How the visualizer handles large fabrics

This document explains, in plain language, how the InfraGraph visualizer draws
very large topologies quickly, and how the **compression** feature works.

It is written for someone who has never read the code. Every number in here is
measured from the sample fabrics in the repository root.

---

## 1. The problem

A 4096 rank Clos fabric turns into a graph with **5376 nodes and 20480 edges**.
Handing that straight to a browser used to take about **6 seconds** before the
picture appeared, and panning was jerky afterwards.

Three separate things were slow, and they needed three separate fixes:

| Problem | Fix | Section |
| --- | --- | --- |
| The browser was computing where every node goes | Work it out in Python instead | [2](#2-positions-are-worked-out-in-python) |
| Shadows, curved edges and text outlines redrawn every frame | Simplify the drawing when the graph is big | [3](#3-simplified-drawing-for-big-graphs) |
| Thousands of nodes on screen at once | Merge the ones that are identical | [4](#4-compression) |

---

## 2. Positions are worked out in Python

### What a layout engine is

Give a graph library a list of boxes and a list of wires, with no coordinates,
and it has to *invent* the coordinates. That code is called a layout engine.
The one built into vis-network runs in the browser, every time you open the
page, and its cost grows roughly with the square of the node count.

### What we do instead

The generator now computes the position of every node and writes it into the
data file:

```json
{"id": "server_0", "label": "server[0]", "level": 0, "x": -245700, "y": 0}
```

With `x` and `y` already filled in there is nothing left to decide, so the
browser turns its layout engine and its physics simulation off completely and
becomes a plain renderer. Draw this icon here, draw a line between those two
points, done.

Think of it as the difference between posting someone a finished seating chart
and posting them a guest list with a note saying who must sit near whom.

```
512 rank fabric,  time until the graph is usable

   layout computed in the browser    5.8 s
   layout computed in Python         0.59 s
```

### How the positions are chosen

`Visualizer._compute_layout` in `visualize.py` does three things:

1. **Find the rows.** Starting from the hosts, walk outward one hop at a time.
   Servers are row 0, the switches they plug into are row 1, and so on.
2. **Place each row, bottom upward.** A switch wants to sit at the average
   horizontal position of the things beneath it, so it ends up centred over its
   own servers. Where two nodes want the same spot they are nudged apart, and
   the whole row is then re-centred. This is a classic technique called the
   barycentre heuristic.
3. **Choose the vertical gap** between rows from the width of the widest row,
   aiming for a drawing about four times wider than it is tall.

The payoff is visible in the result. For the 512 rank fabric every one of the
128 leaf switches ends up **exactly** above the average position of its four
servers, so the wires run straight up and never cross.

> Device drill-down views such as `switch.json` deliberately do **not** get
> precomputed positions. They only have 8 to 33 nodes, so the browser's own
> engine is instant there and produces a nicer left-to-right arrangement.
> The frontend decides per view by simply asking whether the nodes carry
> coordinates.

---

## 3. Simplified drawing for big graphs

Once a view passes **300 nodes or 1000 edges**, the frontend drops the
expensive decoration:

* straight edges instead of curved ones
* no edge labels, the `×N` count moves into the tooltip
* no drop shadows on nodes
* no outline around label text
* hover highlighting off, because it repaints the whole canvas

The result is roughly a **40 percent cheaper redraw**, which is what makes
panning feel smooth. There is a "Simplified rendering" checkbox in the Controls
panel if you want to force it on or off for a particular view.

---

## 4. Compression

### 4.1 The one rule

> **If two boxes plug into the same things above them, draw one box instead of
> two.**

More precisely, two nodes are merged when all three of these are true:

1. they belong to the same instance group, so servers never merge with switches
2. they sit on the same row
3. they connect to exactly the same set of nodes one row up

Nodes at the very top have nothing above them, so for those the rule flips and
they are grouped by what is *below* them instead.

### 4.2 A worked example

`clos.yaml` in the repository root is small enough to follow completely.
It has 8 servers, 8 tier_0 switches, 8 tier_1 switches and 4 tier_2 switches,
which is **28 nodes and 40 edges**.

Working bottom upward:

```
row 0   8 servers    nothing merges.
                     Each server has its own private tier_0 uplink,
                     so no two of them look alike.

row 1   8 tier_0     merges into 4 pairs.
                     tier_0_0 and tier_0_1 both plug into {tier_1_0, tier_1_1},
                     so they are interchangeable.

row 2   8 tier_1     merges into 2 groups of 4.
                     {0, 2, 4, 6} all plug into {tier_2_0, tier_2_1}
                     {1, 3, 5, 7} all plug into {tier_2_2, tier_2_3}

row 3   4 tier_2     merges into 2 pairs.
                     Nothing above them, so they are grouped by what is below,
                     and the pair 0,1 share the same tier_1 group.
```

Two details worth noticing.

**Row 2 merges switches that are not next to each other.** Switch 0 goes with
switch 2, not with switch 1. That is not a quirk of the code, it is the wiring.
This is where the odd looking `tier_1 ×4` labels come from, explained in
[section 6](#6-why-some-labels-say-n-instead-of-a-range).

**Row 3 has to run last.** Its rule needs to know which groups row 2 formed, so
the whole pass must go bottom upward.

### 4.3 Edges are merged too

Once nodes are merged, many wires now join the same pair of boxes. Those are
folded into one line carrying a running total:

```
before   28 nodes, 40 edges
after    16 nodes, 18 edges

one merged line:   tier_1 group  to  tier_2 group,  labelled  "×8 tier_1_link"
```

The `×8` means eight real cables are represented by that single line. The totals
always add up, no matter how far you compress, which is how you can trust the
picture.

### 4.4 The slider, and why there is more than one step

Running the rule once is not the end, because **merging changes the answer to
its own question**. After the tier_0 switches paired up, `server_0` and
`server_1` now plug into the *same box*, when previously they plugged into two
different boxes. They have become interchangeable.

So the generator feeds the result back in and runs the rule again, and keeps
going until a pass changes nothing. Each pass becomes one step on the
compression slider:

```
clos.yaml

  original   28 nodes, 40 edges
  step 1     16 nodes, 18 edges
  step 2      9 nodes,  8 edges     the servers now pair up
  step 3      6 nodes,  5 edges
  step 4      4 nodes,  3 edges     see below
```

The **last step is different**. It ignores wiring entirely and merges everything
that shares an instance group and a row, giving exactly one box per tier. It
answers "what tiers exist and how big are they" rather than "how is this wired",
which is why it sits at the far right of the slider.

Compression is only generated for fabrics with **more than 128 hosts**.
Anything smaller is readable as it is.

---

## 5. Why the leaf switches collapse into one box

This surprises everybody, so it gets its own section. Here is the 1k fabric:

| Slider step | servers | tier_0 | tier_1 | tier_2 | total nodes |
| --- | --- | --- | --- | --- | --- |
| original | 1000 | 200 | 200 | 100 | 1500 |
| 1 | 200 | 20 | 10 | 10 | 240 |
| 2 | 20 | **1** | 10 | 10 | 41 |
| 3 | 1 | 1 | 10 | 10 | 22 |
| 4 | 1 | 1 | 1 | 1 | 4 |

At step 2 all 200 leaf switches become a single box. The reason is that the
spines above them were merged first, and that erased the only difference the
leaves had.

```
Round 0, the real wiring
  pod A leaves plug into spines 1 and 2
  pod B leaves plug into spines 3 and 4
  Different, so the leaves stay separate. This is step 1.

Round 1, the spines get merged
  spine 1 and spine 3 do the same job in their own pod, so they become box X
  spine 2 and spine 4 become box Y

Round 2, look at the leaves again
  pod A leaves plug into X and Y
  pod B leaves plug into X and Y
  Identical now, so every leaf in the fabric merges into one box.
```

Measured on the real graph, the leaves had **20** different uplink patterns
before the spines were merged, and **1** afterwards.

This is the rule working correctly, but it has a practical consequence worth
remembering:

> **Step 1 is the last view where pod structure is visible.**
> Steps 2 and beyond describe scale, not wiring.

A fat tree is especially prone to this because it is deliberately uniform.
Every pod reaches every plane by design, so once the planes are collapsed the
pods become indistinguishable.

---

## 6. Why some labels say `×N` instead of a range

A group label has to tell you *which* nodes are inside. Two forms are used:

```
tier_2[0..15]     members are 0, 1, 2, 3 ... 15        step of 1, consecutive
tier_1 ×32        members are 0, 16, 32, 48 ... 496    step of 16, not consecutive
```

The range form is only used when it is literally true. Writing
`tier_1[0..496]` would claim the box holds 497 switches when it holds 32, so
the code falls back to a plain count.

The stride is real. In the 4k fabric the 512 tier_1 switches are arranged as
32 pods of 16, and the switch number encodes both as `pod * 16 + plane`.
Grouping by shared uplinks collects one switch from every pod, all in the same
plane, so you get every 16th switch.

Known rough edge: every such group reads `tier_1 ×32`, so sixteen of them look
identical on screen. A stride form such as `tier_1[0..496 step 16]` would be
both true and specific. Not implemented yet.

---

## 7. Racks and pods

A group is labelled from what the data says, never from an assumption:

| Label | Meaning |
| --- | --- |
| **rack** | a bottom row group whose members all uplink to exactly one switch |
| **pod** | several such racks merged, the tooltip says how many |
| **group** | anything on a higher row, since a spine group is not a rack |

On the 4k fabric, step 1 produces 512 racks and step 2 produces 32 pods. A rack
tooltip reads:

```
Rack: 8 × server
Uplink: tier_0[0]
Device: server
Members: server[0], server[1], ... server[7]
```

---

## 8. Opening a rack

Clicking a rack or pod opens it. You see **its actual member servers together
with the switches they uplink to**, not a generic device template:

```
Infrastructure  ›  Rack server[0..7]  ›  server[0]
   512 racks         8 servers + tier_0[0]      cpu, xpu, nic, pcie
```

Each click reveals one more layer, which is what a breadcrumb should do. A hop
slider appears in the header while you are inside a rack and controls how much
surrounding fabric comes along:

```
1 hop     8 servers + their tier_0 switch          9 nodes
2 hops    plus the 16 tier_1 spines above          25 nodes
```

Members are drawn normally and the surrounding context switches are faded, so
it is clear which nodes are the subject.

Two deliberate restrictions:

**Only servers open as racks.** Clicking a switch group goes straight to the
shared device template, because every switch in a group is an instance of the
same device and seeing 512 identical copies tells you nothing. This also removed
the two slowest cases, one of which took 83 seconds.

**Very large groups will not open.** If the view would exceed **250 nodes** the
cursor becomes `not-allowed`, the tooltip explains why, and clicking shows a
short message instead. At the highest compression a single box can stand for
every server in the fabric, and expanding it would build thousands of nodes and
take about 90 seconds.

```
opening a rack                88 ms
opening a switch group        86 ms   (the device template)
opening a 4096 server pod     refused
```

A rack view is built in the browser from data that already ships, so no extra
files are generated and the data file does not grow. It uses the same
barycentre placement as the main view, ported to JavaScript, because
vis-network's own engine stretched larger rack views by more than ten times.

---

## 9. Things you can tune

### In `visualize.py`

| Constant | Default | Effect |
| --- | --- | --- |
| `COMPRESS_MIN_HOSTS` | 128 | below this, no compression is generated |
| `LAYOUT_NODE_SPACING` | 120 | horizontal gap in the main view |
| `LAYOUT_GROUP_SPACING` | 320 | horizontal gap in compressed views |
| `LAYOUT_ASPECT` | 4.0 | target width divided by height, **raise it to reduce the vertical gap** |
| `LAYOUT_MIN_LEVEL_SEP` | 150 | floor on the vertical gap |
| `LAYOUT_MAX_LEVEL_SEP` | 6000 | ceiling on the vertical gap |

The vertical gap is `min(max(width / (ASPECT * rows), MIN), MAX)`. Only one of
the three is in charge for any given view, so check which before changing
anything. For the full 4k view and step 1 the **ceiling** is in charge, so
raising `LAYOUT_ASPECT` there does nothing and you must lower
`LAYOUT_MAX_LEVEL_SEP`.

Changes here require regenerating.

### In the frontend

| Where | Default | Effect |
| --- | --- | --- |
| `network.js` `LARGE_GRAPH_NODES` / `LARGE_GRAPH_EDGES` | 300 / 1000 | when simplified drawing switches on |
| `navigation.js` `RACK_MAX_NODES` | 250 | largest rack view that may be opened |
| `navigation.js` divisor in `layoutSubgraph` | 2 | vertical gap in rack views, same idea as `LAYOUT_ASPECT` |
| `network.js` `internalOptions.levelSeparation` | 180 | vertical gap in device drill-down views |

The Controls panel also has live sliders for node spacing and level separation,
which is the quickest way to experiment without editing anything.

> The frontend files are copied into the output directory when you generate, so
> for quick experiments you can edit `viz/js/*.js` and just refresh the browser.
> Copy your final values back into the source, or the next generate will
> overwrite them.

---

## 10. Glossary

| Term | Meaning |
| --- | --- |
| **row** / level | how many hops a node is from the servers. Servers are row 0 |
| **step** | one position on the compression slider |
| **group node** | a single box standing in for several real nodes |
| **rack** | a group whose members share exactly one uplink switch |
| **pod** | several racks merged into one box |
| **hop** | how far out from a rack the surrounding fabric is included |
| **barycentre** | placing a node at the average position of its neighbours below |

---

## 11. Where the code lives

| File | Responsibility |
| --- | --- |
| `visualize.py` | builds all views, computes positions, does the compression |
| `frontend/js/network.js` | chooses which drawing mode a view gets |
| `frontend/js/data.js` | turns the generated JSON into vis-network objects |
| `frontend/js/navigation.js` | breadcrumb, compression slider, rack views |
| `frontend/js/app.js` | renders, handles clicks and hover |
| `frontend/js/controller.js` | the Controls panel sliders |
| `frontend/js/filters.js`, `search.js` | filter panel and node search |
