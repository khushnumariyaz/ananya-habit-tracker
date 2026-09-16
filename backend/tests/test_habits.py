from datetime import date


def test_habit_lifecycle_and_schedule(client):
	response = client.post(
		"/api/habits",
		json={
			"name": "Read",
			"description": "Ten pages",
			"start_date": "2026-09-14",
			"frequency_type": "custom",
			"days_of_week": [0, 2, 4],
		},
	)

	assert response.status_code == 201
	habit = response.json()
	assert habit["days_of_week"] == [0, 2, 4]

	assert client.get("/api/today", params={"date": "2026-09-15"}).json()["habits"] == []
	assert client.get("/api/today", params={"date": "2026-09-16"}).json()["habits"][0]["name"] == "Read"

	habit_id = habit["id"]
	archived = client.patch(f"/api/habits/{habit_id}/archive")
	assert archived.status_code == 200
	assert client.get("/api/habits").json() == []
	assert len(client.get("/api/habits", params={"archived": True}).json()) == 1

	restored = client.patch(f"/api/habits/{habit_id}/restore")
	assert restored.status_code == 200
	assert len(client.get("/api/habits").json()) == 1


def test_update_custom_schedule_requires_a_schedule_when_switching(client):
	habit = client.post(
		"/api/habits",
		json={"name": "Water", "start_date": str(date(2026, 9, 14))},
	).json()

	response = client.put(
		f"/api/habits/{habit['id']}",
		json={"frequency_type": "custom"},
	)

	assert response.status_code == 400


def test_search_and_update_a_habit(client):
	created = client.post(
		"/api/habits",
		json={"name": "Read a book", "start_date": "2026-09-14"},
	)
	habit_id = created.json()["id"]

	assert len(client.get("/api/habits", params={"q": "book"}).json()) == 1
	assert client.get("/api/habits", params={"q": "meditate"}).json() == []

	updated = client.put(
		f"/api/habits/{habit_id}",
		json={"name": "Read ten pages", "description": "Before bed"},
	)

	assert updated.status_code == 200
	assert updated.json()["name"] == "Read ten pages"
	assert updated.json()["description"] == "Before bed"


def test_habit_validation_rejects_invalid_dates_and_missing_custom_days(client):
	bad_dates = client.post(
		"/api/habits",
		json={"name": "No sugar", "start_date": "2026-09-20", "end_date": "2026-09-19"},
	)
	missing_days = client.post(
		"/api/habits",
		json={"name": "Workout", "start_date": "2026-09-14", "frequency_type": "custom"},
	)

	assert bad_dates.status_code == 400
	assert missing_days.status_code == 400


def test_users_cannot_see_or_change_each_others_habits(client):
	other_user = client.post("/api/users", json={"name": "Sam"})
	habit = client.post(
		"/api/habits",
		json={"name": "Private reading", "start_date": "2026-09-14"},
	).json()
	other_headers = {"X-User-ID": str(other_user.json()["id"])}

	assert client.get("/api/habits", headers=other_headers).json() == []
	assert client.get(f"/api/habits/{habit['id']}", headers=other_headers).status_code == 404
	assert client.patch(f"/api/habits/{habit['id']}/archive", headers=other_headers).status_code == 404
	assert client.post(
		"/api/completions",
		json={"habit_id": habit["id"], "date": "2026-09-14"},
		headers=other_headers,
	).status_code == 404

	other_habit = client.post(
		"/api/habits",
		json={"name": "Sam's workout", "start_date": "2026-09-14"},
		headers=other_headers,
	)
	assert other_habit.status_code == 201
	assert [item["name"] for item in client.get("/api/habits").json()] == ["Private reading"]
