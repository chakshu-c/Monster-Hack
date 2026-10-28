print("Starting...")
import pandas as pd

folder = r"C:\Users\chaks\Downloads\OneDrive_8_28-10-2026"

print("Loading...")
lms   = pd.read_csv(folder + r"\la_mmh_training_lms_item_activity_by_session_fact.csv",
                    usecols=["P_ID", "TIMESTAMP", "LMS_ITEM_ID"], dtype={"LMS_ITEM_ID": str})
video = pd.read_csv(folder + r"\la_mmh_training_video_activity_by_view_fact.csv",
                    usecols=["P_ID", "TIMESTAMP", "VIDEO_ID"])

lms["item"]   = "LMS_" + lms["LMS_ITEM_ID"]
video["item"] = "VID_" + video["VIDEO_ID"]
activity = pd.concat([lms[["P_ID", "TIMESTAMP", "item"]], video[["P_ID", "TIMESTAMP", "item"]]])
activity = activity.drop_duplicates()          # ignore a student's own duplicate rows (that's the Phantom)
print("Loaded", len(activity), "rows")

def find_doppelgangers(activity, min_shared=5):
    # 1. Keep only rows where the exact same (time, item) appears more than once
    shared = activity[activity.duplicated(["TIMESTAMP", "item"], keep=False)]

    # 2. For each shared (time, item), which students had it?
    who = shared.groupby(["TIMESTAMP", "item"])["P_ID"].apply(lambda s: tuple(sorted(set(s))))
    who = who[who.apply(len) == 2]              # exactly two different students

    # 3. Count how many rows each pair has in common
    pairs = who.value_counts().reset_index()
    pairs.columns = ["pair", "identical_rows"]
    print("Top pairs:")
    print(pairs.head(15))

    # 4. Keep pairs with lots of identical rows (not coincidence)
    return pairs[pairs["identical_rows"] >= min_shared]

pairs = find_doppelgangers(activity)
print("Number of doppelganger pairs:", len(pairs))

# Each P_ID on its own row, as the guide requires
rows = []
for (p1, p2), n in zip(pairs["pair"], pairs["identical_rows"]):
    rows.append({"P_ID": p1, "Monster": "Doppelganger", "Pair": p2})
    rows.append({"P_ID": p2, "Monster": "Doppelganger", "Pair": p1})
dop = pd.DataFrame(rows)
print(dop)
dop.to_csv(folder + r"\doppelgangers.csv", index=False)
print("Saved doppelgangers.csv")