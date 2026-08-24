from job_search_automation.ats.registry import ATSRegistry


boards = ATSRegistry.boards(
    "lever"
)

for board in boards:
    print(
        board
    )