"""
MINI MONSTER HACK - HUNT (all 9 monsters)

Put ALL the CSVs in one folder (training activity + person + module files AND the 4 *_dim files),
set FOLDER below, then press the Run button.

Outputs (saved into FOLDER/hunt_output):
  HUNT_monsters.xlsx  - sheet "HUNT" = P_ID + Monster (paste into the HUNT Excel template)
                        + one sheet per monster with the evidence table
  table_<monster>.png - picture of each monster's table (top rows) for the slides
  chart_*.png         - summary + example charts
"""
import sys, os, glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FOLDER = r"C:\Users\chaks\Downloads\OneDrive_8_28-10-2026"
DIM_FOLDER = r"C:\Users\chaks\Downloads\OneDrive_5_28-10-2026"   # the 4 *_dim files
if len(sys.argv) > 1:
    FOLDER = DIM_FOLDER = sys.argv[1]

OUT = os.path.join(FOLDER, "hunt_output")
os.makedirs(OUT, exist_ok=True)
pd.set_option("display.width", 200)


def load(name_part, **kwargs):
    """Find the CSV whose file name contains name_part (in either folder) and load it."""
    matches = glob.glob(os.path.join(FOLDER, f"*{name_part}*.csv")) + \
              glob.glob(os.path.join(DIM_FOLDER, f"*{name_part}*.csv")) + \
              glob.glob(os.path.join(DIM_FOLDER, "*", f"*{name_part}*.csv"))
    if not matches:
        sys.exit(f"Can't find a file with '{name_part}' in its name in {FOLDER} or {DIM_FOLDER}")
    return pd.read_csv(matches[0], **kwargs)


# =====================================================================
# LOAD
# =====================================================================
print("Loading files (the big LMS file can take a minute or two)...")
lms = load("lms_item_activity", dtype={"LMS_ITEM_ID": str})
video = load("video_activity")
people = load("person_dim", na_values=["null"])
registrations = load("person_module_instance")
calendar = load("calendar_dim")
modules = load("module_instance_dim")
lms_items = load("lms_item_dim", dtype={"LMS_ITEM_ID": str})
videos = load("video_dim")
print(f"LMS rows: {len(lms):,} | Video rows: {len(video):,} | Students: {len(people):,}")

# One combined activity table: student, date, time, item, source
activity = pd.concat([
    pd.DataFrame({"P_ID": lms.P_ID, "DATE": lms.DATE, "TIMESTAMP": lms.TIMESTAMP,
                  "item": "LMS_" + lms.LMS_ITEM_ID, "row_id": lms.PIT_ID}),
    pd.DataFrame({"P_ID": video.P_ID, "DATE": video.DATE, "TIMESTAMP": video.TIMESTAMP,
                  "item": "VID_" + video.VIDEO_ID, "row_id": video.PVT_ID}),
], ignore_index=True)
activity["time"] = pd.to_datetime(activity.TIMESTAMP, format="ISO8601").dt.tz_localize(None)
activity["date"] = activity.time.dt.normalize()
activity = activity.merge(calendar[["DATE", "WEEK_NUMBER"]], on="DATE", how="left")
activity = activity.sort_values(["P_ID", "time"]).reset_index(drop=True)

# "Clean" version without exact repeats, so Phantom duplicates don't distort other monsters
clean = activity.drop_duplicates(["P_ID", "TIMESTAMP", "item"])
print("Activity table ready\n")

results = []   # (P_ID, Monster)
tables = {}    # monster -> evidence table


def report(monster, table, ids):
    """Print the table, remember it, and add the IDs to the HUNT list."""
    print("=" * 70)
    print(f"{monster.upper()}  ->  {len(ids)} found")
    print("=" * 70)
    print(table.head(15).to_string() if len(table) else "(none)")
    print()
    tables[monster] = table
    for p in ids:
        results.append((p, monster))


# =====================================================================
# 1. PHANTOM - duplicate activity rows
# =====================================================================
def find_phantoms(lms, video):
    lms_dup = lms[lms.PIT_ID.duplicated(keep=False) | lms.drop(columns="PIT_ID").duplicated(keep=False)]
    vid_dup = video[video.PVT_ID.duplicated(keep=False) | video.drop(columns="PVT_ID").duplicated(keep=False)]
    table = pd.concat([lms_dup.groupby("P_ID").size().rename("lms_duplicate_rows"),
                       vid_dup.groupby("P_ID").size().rename("video_duplicate_rows")], axis=1).fillna(0).astype(int)
    table["total"] = table.sum(axis=1)
    return table.sort_values("total", ascending=False)

t = find_phantoms(lms, video)
report("Phantom", t, t.index)


# =====================================================================
# 2. UNDEAD STUDENT - activity after deregistration
# =====================================================================
def find_undead(clean, people):
    last_active = clean.groupby("P_ID").date.max().rename("last_activity")
    left = people.dropna(subset=["deregistration_date"]).set_index("P_ID")
    left["deregistration_date"] = pd.to_datetime(left.deregistration_date)
    left = left.join(last_active)
    table = left[left.last_activity > left.deregistration_date].copy()
    table["days_after_leaving"] = (table.last_activity - table.deregistration_date).dt.days
    return table[["deregistration_date", "last_activity", "days_after_leaving"]].sort_values(
        "days_after_leaving", ascending=False)

t = find_undead(clean, people)
report("Undead Student", t, t.index)


# =====================================================================
# 3. DOPPELGANGER - pairs of students with identical activity
# =====================================================================
def find_doppelgangers(clean, min_shared=5):
    shared = clean[clean.duplicated(["TIMESTAMP", "item"], keep=False)]
    who = shared.groupby(["TIMESTAMP", "item"]).P_ID.agg(lambda s: tuple(sorted(set(s))))
    who = who[who.map(len) == 2]
    pairs = who.value_counts()
    all_pairs = pd.DataFrame([(a, b, n) for (a, b), n in pairs.items()],
                             columns=["P_ID_1", "P_ID_2", "identical_rows"])
    # Sanity check: how many pairs share 1, 2, 3... rows? Real doppelgangers should sit far above the rest
    print("(Doppelganger check - number of pairs by shared rows:",
          all_pairs.identical_rows.clip(upper=10).value_counts().sort_index().to_dict(), " [10 = 10+])")
    return all_pairs[all_pairs.identical_rows >= min_shared]

t = find_doppelgangers(clean)
report("Doppelganger", t, list(t.P_ID_1) + list(t.P_ID_2))   # both IDs, separate rows


# =====================================================================
# 4. SHAPE-SHIFTER - activity in a department they're not registered in
# =====================================================================
def find_shapeshifters(activity):
    item_module = pd.concat([
        lms_items.assign(item="LMS_" + lms_items.LMS_ITEM_ID)[["item", "MODULE_INSTANCE_ID"]],
        videos.assign(item="VID_" + videos.VIDEO_ID)[["item", "MODULE_INSTANCE_ID"]]])
    a = activity[["P_ID", "item", "row_id"]].merge(item_module, on="item", how="left") \
        .merge(modules[["MODULE_INSTANCE_ID", "DEPARTMENT_ID"]], on="MODULE_INSTANCE_ID", how="left")

    reg = registrations.merge(modules[["MODULE_INSTANCE_ID", "DEPARTMENT_ID"]], on="MODULE_INSTANCE_ID")
    registered = set(zip(reg.P_ID, reg.DEPARTMENT_ID))

    a["outside_dept"] = [(p, d) not in registered and pd.notna(d) for p, d in zip(a.P_ID, a.DEPARTMENT_ID)]
    a["copy_row"] = a.row_id.astype(str).str.contains("_COPY_")

    table = a.groupby("P_ID").agg(rows=("item", "size"), outside_dept_rows=("outside_dept", "sum"),
                                  copy_rows=("copy_row", "sum"))
    table = table[table.index.isin(reg.P_ID)]               # must have registrations
    table["outside_share"] = (table.outside_dept_rows / table.rows).round(3)
    return table[table.copy_rows > 0].sort_values("copy_rows", ascending=False)

t = find_shapeshifters(activity)
report("Shape-shifter", t, t.index)


# =====================================================================
# 5. GHOST - active early, then disappears
# =====================================================================
weekly = clean.groupby(["P_ID", "WEEK_NUMBER"]).size().unstack(fill_value=0) \
              .reindex(columns=range(1, 53), fill_value=0)

def find_ghosts(weekly):
    early = weekly[[1, 2, 3, 4]]
    early_avg = early.mean(axis=1)
    later_avg = weekly.loc[:, 5:].mean(axis=1)
    ratio = later_avg / early_avg                      # computed BEFORE any rounding
    table = pd.DataFrame({
        "active_weeks_1to4": (early > 0).sum(axis=1),
        "early_weekly_avg": early_avg.round(2),
        "later_weekly_avg": later_avg.round(2),
        "later_vs_early": ratio.round(4)})
    keep = ((early > 0).sum(axis=1) >= 3) & (ratio < 0.10)
    return table[keep].sort_values("later_vs_early")

t = find_ghosts(weekly)
deregistered = set(people.dropna(subset=["deregistration_date"]).P_ID)
print(f"(Ghost: excluding {t.index.isin(deregistered).sum()} students who deregistered - they left, they're not haunting)")
t = t[~t.index.isin(deregistered)]          # students who officially left aren't ghosts
report("Ghost", t, t.index)


# =====================================================================
# 6. ZOMBIE - continuous activity (no gap > 15 min) for more than 3 hours
# =====================================================================
def find_zombies(clean):
    gap = clean.groupby("P_ID").time.diff()
    new_run = gap.isna() | (gap > pd.Timedelta(minutes=15))
    run_id = new_run.cumsum()
    runs = clean.groupby(["P_ID", run_id]).time.agg(start="min", end="max", rows="size")
    runs["hours"] = ((runs.end - runs.start).dt.total_seconds() / 3600).round(2)
    longest = runs.sort_values("hours", ascending=False).reset_index().drop_duplicates("P_ID").set_index("P_ID")
    return longest[["start", "end", "rows", "hours"]], longest[longest.hours > 3]

top_runs, t = find_zombies(clean)
report("Zombie", t, t.index)
tables["Zombie (top runs)"] = top_runs.head(20)


# =====================================================================
# 7. VAMPIRE - more night days than day days, > 21 night days
# =====================================================================
def find_vampires(clean):
    # Guide: night = "> midnight to 5am", day = "> 5am to midnight"
    # so 00:00:00 exactly counts as DAY and 05:00:00 exactly counts as NIGHT
    t = clean.time
    seconds = t.dt.hour * 3600 + t.dt.minute * 60 + t.dt.second + t.dt.microsecond / 1e6
    is_night = (seconds > 0) & (seconds <= 5 * 3600)
    table = pd.DataFrame({
        "night_days": clean[is_night].groupby("P_ID").date.nunique(),
        "day_days": clean[~is_night].groupby("P_ID").date.nunique()}).fillna(0).astype(int)
    return table[(table.night_days > table.day_days) & (table.night_days > 21)].sort_values(
        "night_days", ascending=False)

t = find_vampires(clean)
report("Vampire", t, t.index)


# =====================================================================
# 8. WEB CRAWLER - > 200 different items/videos in a 12-hour block
# =====================================================================
def find_web_crawlers(clean, limit=200):
    block = clean.time.dt.floor("12h")
    per_block = clean.groupby(["P_ID", block]).item.nunique().rename("items_in_12h_block").reset_index()
    busiest = per_block.sort_values("items_in_12h_block", ascending=False).drop_duplicates("P_ID").set_index("P_ID")
    busiest = busiest.rename(columns={"time": "block_start"})

    # Sensitivity check: ANY 12-hour window (rolling), for the 60 busiest students only (fast)
    rolling = {}
    for pid in busiest.head(60).index:
        d = clean[clean.P_ID == pid]
        t, items = d.time.values, d.item.values
        end = np.searchsorted(t, t + np.timedelta64(12, "h"))
        rolling[pid] = max(len(set(items[i:end[i]])) for i in range(len(t)))
    busiest["any_12h_window"] = pd.Series(rolling)
    extra = busiest[(busiest.items_in_12h_block <= limit) & (busiest.any_12h_window > limit)]
    print(f"(Web Crawler check - students who'd ALSO count if 'block' meant any 12h window: {len(extra)})")
    return busiest, busiest[busiest.items_in_12h_block > limit]

top_blocks, t = find_web_crawlers(clean)
report("Web Crawler", t, t.index)
tables["Web Crawler (top blocks)"] = top_blocks.head(20)


# =====================================================================
# 9. WEREWOLF - repeated spikes in Autumn AND Spring
# =====================================================================
def find_werewolves(clean):
    # Term dates come from the hack's own calendar_dim, not hard-coded
    term_dates = calendar.groupby("TERM").DATE.agg(["min", "max"])
    autumn_start, autumn_end = term_dates.loc["Autumn", "min"], term_dates.loc["Autumn", "max"]
    spring_end = term_dates.loc["Spring", "max"]
    print(f"(Werewolf: Autumn {autumn_start} to {autumn_end}, Spring to {spring_end})")

    daily = clean.groupby(["P_ID", "date"]).size()
    rows = []
    for pid, s in daily.groupby(level=0):
        s = s.droplevel(0).reindex(pd.date_range(autumn_start, spring_end), fill_value=0)
        active = s[s > 0]
        if len(active) < 10:
            continue
        threshold = max(5 * active.median(), s.mean() + 4 * s.std())   # a "spike" day
        spikes = s[s > threshold]
        rows.append({"P_ID": pid,
                     "autumn_spikes": int((spikes.index <= autumn_end).sum()),
                     "spring_spikes": int((spikes.index > autumn_end).sum()),
                     "biggest_day": int(s.max()),
                     "normal_active_day": float(active.median())})
    table = pd.DataFrame(rows).set_index("P_ID")
    table["total_spikes"] = table.autumn_spikes + table.spring_spikes
    table = table.sort_values(["total_spikes", "biggest_day"], ascending=False)
    return table, table[(table.autumn_spikes >= 2) & (table.spring_spikes >= 2)]

candidates, t = find_werewolves(clean)
report("Werewolf", t, t.index)
tables["Werewolf (candidates)"] = candidates.head(20)   # CHECK THESE BY EYE


# =====================================================================
# SAVE
# =====================================================================
hunt = pd.DataFrame(results, columns=["P_ID", "Monster"]).drop_duplicates()
summary = hunt.Monster.value_counts().rename_axis("Monster").reset_index(name="students")

print("=" * 70)
print("HUNT SUMMARY")
print("=" * 70)
print(summary.to_string(index=False))

xlsx = os.path.join(OUT, "HUNT_monsters.xlsx")
with pd.ExcelWriter(xlsx) as writer:
    hunt.sort_values(["Monster", "P_ID"]).to_excel(writer, sheet_name="HUNT", index=False)
    summary.to_excel(writer, sheet_name="Summary", index=False)
    for name, table in tables.items():
        table.reset_index().to_excel(writer, sheet_name=name[:31], index=False)


def table_png(name, table, max_rows=12):
    """Save a monster's table as a picture for the slides."""
    if not len(table):
        return
    show = table.head(max_rows).reset_index()
    show = show.apply(lambda c: c.dt.strftime("%Y-%m-%d %H:%M") if pd.api.types.is_datetime64_any_dtype(c) else c)
    fig, ax = plt.subplots(figsize=(min(2 + 1.8 * show.shape[1], 14), 0.45 * len(show) + 1.2))
    ax.axis("off")
    tb = ax.table(cellText=show.values, colLabels=show.columns, loc="center", cellLoc="center")
    tb.auto_set_font_size(False); tb.set_fontsize(10); tb.scale(1, 1.4)
    for (r, c), cell in tb.get_celld().items():
        if r == 0:
            cell.set_facecolor("#5ad1d3"); cell.set_text_props(weight="bold")
    ax.set_title(f"{name} - evidence (top {len(show)})", fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"table_{name.replace(' ', '_').replace('(', '').replace(')', '')}.png"), dpi=160)
    plt.close(fig)

for name, table in tables.items():
    table_png(name, table)

# Summary chart
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(summary.Monster, summary.students, color="#5ad1d3")
ax.invert_yaxis()
for i, n in enumerate(summary.students):
    ax.text(n, i, f" {n}", va="center")
ax.set_title("Monsters found in the 80% training data"); ax.set_xlabel("students")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "chart_summary.png"), dpi=160); plt.close(fig)

# Vampire example: activity by hour
if len(tables["Vampire"]):
    pid = tables["Vampire"].index[0]
    hours = clean[clean.P_ID == pid].time.dt.hour.value_counts().reindex(range(24), fill_value=0)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(hours.index, hours.values, color="#f0883e")
    ax.axvspan(-0.5, 4.5, color="#5ad1d3", alpha=0.2, label="night (0-5am)")
    ax.set_title(f"Vampire {pid}: activity by hour of day"); ax.set_xlabel("hour"); ax.set_ylabel("activity rows")
    ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(OUT, "chart_vampire_example.png"), dpi=160); plt.close(fig)

# Ghost example: weekly activity
if len(tables["Ghost"]):
    pid = tables["Ghost"].index[0]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(weekly.columns, weekly.loc[pid], color="#f0883e")
    ax.axvspan(0.5, 4.5, color="#5ad1d3", alpha=0.2, label="weeks 1-4")
    ax.set_title(f"Ghost {pid}: busy early, then vanishes"); ax.set_xlabel("academic week"); ax.set_ylabel("activity rows")
    ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(OUT, "chart_ghost_example.png"), dpi=160); plt.close(fig)

print(f"\nSaved everything to: {OUT}")