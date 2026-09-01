# Xbox and PlayStation Console Activity Charts & Plotting Suite

This project is a data archiving and visualization pipeline designed to track, compile, and analyze the popularity of video games on modern Xbox and PlayStation console networks. 

Rather than relying on speculative estimates, this archive is built on empirical, unique player activity records compiled via continuous stochastic sampling of public player profiles. The repository contains both the historical database compilations and a lightweight, offline-capable Python plotting suite to explore and compare these trends.

The historical records contained in this archive currently go back to:
*   **Xbox**: Starting **February 10, 2026**
*   **PlayStation**: Starting **June 10, 2026**

---

### Table of contents
1.  **Section 1: Interaction with the PlayStation and Xbox APIs**  
2.  **Section 2: Chart Compilation**  
3.  **Section 3: Plotting Suite**  


# 1 - Interaction with the Playstation and Xbox APIs

## A. Data Collection: Blind Sampling vs. Presence Filtering

Because the two console networks limit request rates differently, each platform requires a distinct strategy to capture an accurate snapshot of active players.

```
PLAYSTATION METHOD (High-volume blind walks)
[Random Scan] ──> [10,000+ Histories/hr] ──> [Filter Active Players Afterwards]

XBOX METHOD (Low-volume targeted presence scans)
[750,000 Presence Probes/hr] ──> [Select Active 24h Console Players] ──> [Query 2,000 Histories/hr]
```

### PlayStation: The High-Volume Blind Approach
The PlayStation network allows the system to query a large volume of profile histories quickly, allowing the scouts to pull more than **10,000 complete game histories per hour**. 

Because of this high threshold, the system can use a "blind" sampling method. It selects accounts at random from the database and reads their play history. Within a typical hour of blind scanning, this yields:
*   **~1,500 players** who were active in the last 24 hours.
*   **~2,500 players** who were active in the last week.
*   **Over 3,000 players** who were active in the last month.

Over time, as private or permanently inactive accounts are identified and set aside, this yield rate will continue to rise. Even under current baseline settings, this raw volume produces a statistically significant sample of active trends.

### Xbox: Slower Scans & High-Speed Presence Filtering
The Xbox network restricts detailed title history queries much more strictly, limiting scouts to roughly **2,000 game histories per hour**. A blind sampling method on Xbox would be inefficient, yielding too few active players to compile meaningful charts.

However, Xbox offers an alternative: a high-speed batch lookup that returns a player's **online presence** (whether they are online, when they were last seen, and what device they are using, such as Xbox One, Series X|S, Windows, or mobile devices). The system can run these lightweight presence checks on roughly **750,000 accounts per hour**.

The system utilizes this difference to optimize its dataset:
1.  **Presence Scouting**: The system sweeps hundreds of thousands of accounts to find who was active in the last 24 hours on an Xbox One or Xbox Series console.
2.  **Targeted History Queries**: The system selects randomly from this pre-filtered group of active users to perform the slower, detailed game history scans.

#### Methodological Trade-offs & Validation
This targeted approach introduces a potential bias: it naturally favors players who are active almost daily, which may slightly overrepresent highly active players in weekly (7-day) charts. A mathematically stratified approach could be used, but this would introduce complex assumptions that might introduce other biases.

Despite this limitation, comparing these 7-day compiled charts with the official "Most Played" rankings on Xbox.com shows a strong overlap in trends, confirming the data is representative for most major titles (see a gallery of examples in `results_vs_xbox_com.md`). The minor variations that do occur are expected and can be attributed to:
1.  **Global vs. Regional Differences**: The compiled dataset is global, whereas the official storefront charts represent specific regions (like the US).
2.  **Stochastic Sampling**: Data collection is a continuous, probabilistic sampling process, which naturally introduces minor statistical variations.
3.  **Data Latency**: The system collects profiles incrementally over time, meaning some accounts may have slightly older snapshots at the moment of compilation, while Microsoft operates on a single, real-time snapshot of the entire network.

---

## B. Discovering the Network (Friend List Crawling)

To find new accounts, the system relies on a chain-referral system by scanning the friends lists of known players. However, this process faces different limitations on each network.

### Xbox: Public Circles, Low Volume
The Xbox network strictly limits friend list requests, allowing only **600 to 800 friend list scans per hour**. However, privacy settings on Xbox default to public, meaning almost every targeted query returns a complete list of friends, which helps maintain a steady flow of new accounts.

### PlayStation: Private Circles, High Volume
The PlayStation crawler operates at a much higher speed but faces a strict privacy barrier: **over 75% of PlayStation profiles have restricted friend list visibility** (often set to "friends of friends" by default). 

While a few highly public accounts with hundreds of friends help keep the discovery pipeline moving, some isolated areas of the PlayStation network can be difficult to find. For example, if a small group of friends all use restricted privacy settings, the system may never find a path to discover them.

### The Universal Blind Spot
Both crawlers share a common limitation: **isolated players with zero friends cannot be discovered** using a friend-referral system. Because these accounts have no outward-facing connections, their total volume and behavior remain outside the system's tracking loop.

---

## C. Current Database Statistics

The differences in discovery speeds, API limits, and default platform privacy settings have shaped two distinct datasets:

### Xbox Database Profile
*   **Total Discovered Accounts**: 121 Million
*   **Active in the Last Month**: 28 Million
*   **Active in the Last Year**: 48 Million
*   **Unknown Presence Status**: ~50 Million accounts. This includes accounts with hidden online status, restricted privacy settings, or those inactive since April 2023 (when Microsoft cleared historical presence logs).
*   **Network Growth**: ~6,000 to 7,000 newly discovered accounts are added to the directory every hour.

### PlayStation Database Profile
*   **Total Discovered Accounts**: 92 Million
*   **History Privacy Settings**: 23% of accounts have set their game play history to private.
*   **Inactive/Empty Accounts**: 12% are public but show no recorded gameplay history.
*   **Active Demographics**:
    *   ~14% active in the last 24 hours.
    *   ~27% active in the last month.
    *   ~36% active in the last year.
*   **Network Growth**: ~25,000 newly discovered accounts are added to the directory every hour.

---

# 2 - Chart Compilation

Below is a conceptual overview comparing the data collection methodologies, network discovery constraints, and current statistical profiles of the Xbox and PlayStation tracking systems.

---

Here is a high-level, non-technical recap explaining how the raw profile scans are translated into daily and weekly charts, along with the logic behind the statistical filters and Xbox chart variations.

---

## How Raw Data is Translated into Charts

Every day, the system looks at the raw player profiles collected by our automated scouts and organizes them into structured scoreboard files (CSVs). 

To do this fairly, the system uses two main chart types and a critical statistical safeguard to prevent inactive games from distorting the results.

---

### A. Daily vs. Weekly (7-Day Trailing) Charts
The system creates two distinct types of scoreboards to measure game popularity over different timeframes:

*   **Daily Charts (e.g., `daily/2026-08-30.csv`)**: 
    This is a strict 24-hour snapshot [1]. It acts as a targeted window, recording play activity that occurred *only* on that specific calendar day (August 30, 2026).
*   **Weekly Trailing Charts (e.g., `7_days/2026-08-30.csv`)**: 
    This is a rolling, cumulative scoreboard. Instead of looking at a single day, it aggregates player activity over a trailing 7-day period (August 30, 2026, plus the 6 preceding days, covering August 24 through August 30). This smooths out daily fluctuations and provides a broader view of weekly trends.
*   **Recent Release Highlights** (e.g., `7_days/2026-08-30_recent.csv`):
A filtered companion to the primary chart. It contains the exact same user metrics as the parent file, but is reduced to isolate and highlight newly launched games—specifically those with an official release date falling within 30 days prior (or up to 10 days after - for "advanced access" titles) the chart's reference date.

---

### B. The Safeguard Against "Abandoned Games" (Session Deltas)
When the system scans a player's profile, it can only see a single piece of information for each game: **the timestamp of the last time they played it.** 

This introduces a significant statistical challenge, which we solve by enforcing a strict time limit (a "delta" of 3 days for daily charts and 7 days for weekly charts) between when a game was played and when the player's profile was scanned.

Without this limit, the overall charts would become heavily distorted:

*   **The Live-Service Game Catch**: If a user plays a live-service game (like *Fortnite*) every single day, their profile only ever displays one "last played" record. No matter how many times they log in, they only generate one active entry in our database at any given time.
*   **The Abandoned Game Problem**: If a user plays a single-player game once, dislikes it, and abandons it forever, that "last played" timestamp remains frozen on their profile. 
*   **The Distortion**: If we did not limit the time gap between playing a game and scanning the profile, these frozen, abandoned sessions would accumulate in the database over weeks and months. Eventually, abandoned games would crowd out continuously played live-service games, making dead games appear highly active.
*   **The Solution**: By enforcing a short cutoff window, we automatically discard frozen, old sessions. This ensures we are only counting players who are actively engaged with a game near the time of our scan.

---

### C. Xbox Chart Variations: Grouped vs. Ungrouped

Because games are often sold in multiple editions or separate regional packages, we compile the 7-day Xbox charts in two different formats to serve different analytical needs:

*   **Grouped Charts (Hiding Demos/Betas)**: 
    This format combines all different editions of a game (such as standard editions, deluxe bundles, or regional stacked releases) into a single master title. It also filters out playtests, betas, and demos. 
    *   **Purpose**: Because PlayStation naturally consolidates different game editions under a single master "concept," using the Grouped format on Xbox allows for a **clean, 1:1 comparison against PlayStation trends.**
*   **Ungrouped Charts**: 
    This format keeps every individual release and SKU separate, meaning regional versions or deluxe editions are listed as independent entries on the scoreboard. It does not filter out playtests, betas, nor demos. 
    *   **Purpose**: Because the official public charts on Xbox.com also list game editions separately, this format is used to perform a **direct comparison against Microsoft’s official store charts** to verify the accuracy of our tracking data.


# 3 - Plotting Suite

The project includes a custom plotting suite built on **Python** and **Matplotlib**. It is designed specifically to query the archived CSV directory structure and transform raw historical records into clean, readable performance charts. 

A visual gallery of plots alongside executable code samples can be found in the **`examples.ipynb`** file in the root directory.

### Key Features

*   **Offline Catalog Lookups**: 
    Before plotting a game, you perform a quick manual lookup in the local metadata files (`data_xbox.csv` or `data_ps.csv` / `data_playstation.csv`) to locate the specific ID (`title_id`) for your target game.
*   **Single-Platform & Cross-Platform Comparisons**: 
    *   **Same-Platform**: Compare multiple titles on the same console over a matching timeframe.
    *   **Cross-Platform**: Compare performance between Xbox and PlayStation. While this is primarily used to trace platform differences for the same multiplatform game, you can compare any two arbitrary titles across consoles (such as PlayStation's *SAROS* against Xbox's *Forza Horizon 6*).
*   **Double Y-Axis Metrics (Ranks & Percentages)**: 
    By default, plots display the game's ranking (on an inverted left y-axis where Rank 1 is at the top). Optionally, you can toggle a double y-axis (`double_y=True`) to overlay a second curve showing the exact percentage of the active player base playing that game on the right y-axis.
*   **Launch-Aligned Timelines**: 
    Instead of plotting curves against absolute calendar dates, you can align curves by their launch dates. The library automatically retrieves the game's official release date from local metadata and shifts the x-axis to represent "Days Since Launch," allowing you to compare how different titles performed during their initial release windows.
*   **Advanced Matplotlib Extensibility**: 
    For users familiar with Matplotlib's underlying syntax, you can pass a `custom_hook` function to the plotting styles [1]. This gives you direct access to the active Matplotlib `Axes` object, allowing you to add custom annotations, adjust grid lines, or overlay custom reference thresholds without modifying the library's core rendering engine.