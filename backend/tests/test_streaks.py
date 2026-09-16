def test_completions_are_idempotent_and_streaks_skip_unscheduled_days(client):
	habit = client.post(
		"/api/habits",
		json={
			"name": "Workout",
			"start_date": "2026-09-14",
			"frequency_type": "custom",
			"days_of_week": [0, 2, 4],
		},
	).json()

	for completion_date in ("2026-09-14", "2026-09-16", "2026-09-18"):
		response = client.post(
			"/api/completions",
			json={"habit_id": habit["id"], "date": completion_date},
		)
		assert response.status_code == 201

	duplicate = client.post(
		"/api/completions",
		json={"habit_id": habit["id"], "date": "2026-09-18"},
	)
	assert duplicate.status_code == 201
	assert len(client.get(f"/api/completions/{habit['id']}").json()) == 3

	today = client.get("/api/today", params={"date": "2026-09-18"}).json()
	assert today["habits"][0]["current_streak"] == 3
	assert today["habits"][0]["best_streak"] == 3
	assert today["pending_count"] == 0

	not_scheduled = client.post(
		"/api/completions",
		json={"habit_id": habit["id"], "date": "2026-09-15"},
	)
	assert not_scheduled.status_code == 400


def test_today_reminds_about_pending_habits(client):
	habit = client.post(
		"/api/habits",
		json={"name": "Drink water", "start_date": "2026-09-14"},
	).json()

	today = client.get("/api/today", params={"date": "2026-09-14"}).json()

	assert today["pending_count"] == 1
	assert today["reminder"] == "You have 1 habit left to log today."
	assert today["habits"][0]["id"] == habit["id"]

	completion = client.post(
		"/api/completions",
		json={"habit_id": habit["id"], "date": "2026-09-14"},
	)
	assert completion.status_code == 201
	assert client.get("/api/today", params={"date": "2026-09-14"}).json()["pending_count"] == 0


def test_streak_break_preserves_best_ever_streak(client):
	habit = client.post(
		"/api/habits",
		json={
			"name": "No sugar",
			"start_date": "2026-09-14",
			"frequency_type": "custom",
			"days_of_week": [0, 1, 2, 3, 4],
		},
	).json()

	for completion_date in ("2026-09-14", "2026-09-15", "2026-09-17", "2026-09-18"):
		assert client.post(
			"/api/completions",
			json={"habit_id": habit["id"], "date": completion_date},
		).status_code == 201

	streak = client.get("/api/today", params={"date": "2026-09-18"}).json()["habits"][0]
	assert streak["current_streak"] == 2
	assert streak["best_streak"] == 2

	after_break = client.get("/api/today", params={"date": "2026-09-17"}).json()["habits"][0]
	assert after_break["current_streak"] == 1
	assert after_break["best_streak"] == 2


def test_end_date_stops_scheduling(client):
	habit = client.post(
		"/api/habits",
		json={"name": "75-day challenge", "start_date": "2026-09-14", "end_date": "2026-09-15"},
	).json()

	assert len(client.get("/api/today", params={"date": "2026-09-15"}).json()["habits"]) == 1
	assert client.get("/api/today", params={"date": "2026-09-16"}).json()["habits"] == []
	assert client.post(
		"/api/completions",
		json={"habit_id": habit["id"], "date": "2026-09-16"},
	).status_code == 400
