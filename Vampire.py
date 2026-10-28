print("Starting...")
import pandas as pd
import matplotlib.pyplot as plt

folder = r"C:\Users\chaks\Downloads\OneDrive_8_28-10-2026"

print("Loading LMS (can take 1-2 min)...")
lms = pd.read_csv(folder + r"\la_mmh_training_lms_item_activity_by_session_fact.csv", usecols=["P_ID", "TIMESTAMP"])
print("LMS rows:", len(lms))

print("Loading video...")
video = pd.read_csv(folder + r"\la_mmh_training_video_activity_by_view_fact.csv", usecols=["P_ID", "TIMESTAMP"])
print("Video rows:", len(video))

activity = pd.concat([lms, video])
activity["time"] = pd.to_datetime(activity["TIMESTAMP"], format="ISO8601").dt.tz_localize(None)
activity["date"] = activity["time"].dt.date
print("Timestamps converted")

def find_vampires(activity):
    is_night = activity["time"].dt.hour < 5
    night_days = activity[is_night].groupby("P_ID")["date"].nunique()
    day_days   = activity[~is_night].groupby("P_ID")["date"].nunique()
    counts = pd.DataFrame({"night_days": night_days, "day_days": day_days}).fillna(0)
    vampires = counts[(counts["night_days"] > counts["day_days"]) & (counts["night_days"] > 21)]
    return vampires.sort_values("night_days", ascending=False)

vampires = find_vampires(activity)
print(vampires)
print("Number of vampires:", len(vampires))
vampires.reset_index()[["P_ID"]].assign(Monster="Vampire").to_csv(folder + r"\vampires.csv", index=False)
print("Saved vampires.csv")

example = vampires.index[0]
activity[activity["P_ID"] == example]["time"].dt.hour.value_counts().sort_index().plot.bar(
    title=f"Vampire {example}: activity by hour")
plt.show()