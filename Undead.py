'''Undead found by comparing P_ID and Date against LMS file and Video file, table for each and 1 m,erged'''

import pandas as pd
lms_df = pd.read_csv(r"C:\Users\chell\Downloads\Training\Training\la_mmh_training_lms_item_activity_by_session_fact.csv")
person_df = pd.read_csv(r"C:\Users\chell\Downloads\Training\Training\la_mmh_training_person_dim.csv")
video_df = pd.read_csv(r"C:\Users\chell\Downloads\Training\Training\la_mmh_training_video_activity_by_view_fact.csv", encoding="utf-8-sig")

print(lms_df.shape, person_df.shape, video_df.shape)
print(person_df.columns.tolist())
# 1. keep only rows where deregistration_date is not null
deregistered = person_df[person_df["deregistration_date"].notna()].copy()

# 2. make sure the date column is a real datetime (not text)
deregistered["deregistration_date"] = pd.to_datetime(deregistered["deregistration_date"])

# 3. build the table with just P_ID and deregistration_date
dereg_table = deregistered[["P_ID", "deregistration_date"]].reset_index(drop=True)

print(dereg_table.head())
print(f"Found {len(dereg_table)} deregistered students")

# check LMS column names first
print(lms_df.columns.tolist())

# make sure LMS DATE column is datetime
lms_df["DATE"] = pd.to_datetime(lms_df["DATE"])

# merge dereg_table with lms_df on P_ID
lms_merged = dereg_table.merge(lms_df, on="P_ID", how="left")

# keep only rows where LMS DATE is after deregistration_date
lms_after = lms_merged[lms_merged["DATE"] > lms_merged["deregistration_date"]]

# for each P_ID, take the earliest (first) matching DATE
first_access = lms_after.groupby("P_ID")["DATE"].min().reset_index().rename(
    columns={"DATE": "access_date"}
)

# add access_date back onto dereg_table, keeping all 196 P_IDs
# (P_IDs with no post-deregistration LMS activity will show NaT)
dereg_table = dereg_table.merge(first_access, on="P_ID", how="left")

print(dereg_table.head())
print(f"{dereg_table['access_date'].notna().sum()} students have LMS activity after deregistration")

# check video_df column names
print(video_df.columns.tolist())

# make sure video DATE column is datetime
video_df["DATE"] = pd.to_datetime(video_df["DATE"])

# merge dereg_table with video_df on P_ID
video_merged = dereg_table.merge(video_df, on="P_ID", how="left")

# keep only rows where video DATE is after deregistration_date
video_after = video_merged[video_merged["DATE"] > video_merged["deregistration_date"]]

# for each P_ID, take the earliest (first) matching DATE
first_video_access = video_after.groupby("P_ID")["DATE"].min().reset_index().rename(
    columns={"DATE": "video_access_date"}
)

# add video_access_date back onto dereg_table, keeping all 196 P_IDs
dereg_table = dereg_table.merge(first_video_access, on="P_ID", how="left")

print(dereg_table.head())
print(f"{dereg_table['video_access_date'].notna().sum()} students have video activity after deregistration")

# --- New table: remove rows that have access_date but NO video_access_date ---
final_table = dereg_table[
    ~(dereg_table["access_date"].notna() & dereg_table["video_access_date"].isna())
].copy()

print(final_table)

# --- Summary ---
both_count = final_table[
    final_table["access_date"].notna() & final_table["video_access_date"].notna()
].shape[0]

print(f"{both_count} students have done BOTH LMS and video activity after deregistration")

# --- New table: remove rows that have access_date but NO video_access_date ---
final_table = dereg_table[
    ~(dereg_table["access_date"].notna() & dereg_table["video_access_date"].isna())
].copy()

print(final_table)

# --- Summary ---
both_count = final_table[
    final_table["access_date"].notna() & final_table["video_access_date"].notna()
].shape[0]

print(f"{both_count} students have done BOTH LMS and video activity after deregistration")

# --- New table: students with EITHER access_date or video_access_date present ---
any_activity_table = dereg_table[
    dereg_table["access_date"].notna() | dereg_table["video_access_date"].notna()
].copy()

print(any_activity_table)
print(f"{len(any_activity_table)} students have activity on LMS and/or video after deregistration")
