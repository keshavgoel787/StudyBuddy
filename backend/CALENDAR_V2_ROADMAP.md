# Calendar v2 Implementation Roadmap

## Status: Foundation Complete ✅

### Completed Work
- ✅ Database model: `DayPreferences` with mood/feeling enums
- ✅ Migration: `ae4f57de6a6d_add_day_preferences_table`
- ✅ Schemas: All v2 response models defined in `app/schemas/calendar.py`
- ✅ Schemas: Preferences create/response in `app/schemas/preferences.py`

---

## Remaining Implementation Tasks

### 1. Backend Routes & Logic (Priority 1)

#### A. Preferences Management Routes
**File**: `app/routes/preferences.py` (new)

```python
# GET /preferences/day-preferences?date=YYYY-MM-DD
# Returns user's mood/feeling for specified date (defaults to today)

# POST /preferences/day-preferences
# Body: { "mood": "chill|normal|grind", "feeling": "overwhelmed|okay|on_top", "date"?: "YYYY-MM-DD" }
# Creates or updates preferences for date
```

**Implementation**:
1. Query `DayPreferences` by user_id + date
2. Upsert mood/feeling
3. Invalidate day plan cache for that date
4. Return `DayPreferencesResponse`

---

#### B. Per-Block Planner Routes
**File**: `app/routes/planner.py` (extend existing)

```python
# POST /planner/blocks/{block_id}/skip-today
# Removes the specified assignment block from today's schedule
# Returns updated day plan

# POST /planner/blocks/{block_id}/move
# Body: { "new_start": "ISO datetime" }
# Moves block to new time slot (within today's free blocks)

# POST /planner/blocks/{block_id}/duplicate
# Body: { "target_date": "YYYY-MM-DD" }
# Clones block to another day
```

**Implementation**:
1. Parse block_id format: `"assignment-{assignment_id}-{index}"`
2. For skip: Remove from cached day plan, invalidate cache
3. For move: Validate new time is in free block, update cache
4. For duplicate: Create new block on target date

---

#### C. Week Overview Endpoint
**File**: `app/routes/calendar.py` (extend)

```python
# GET /calendar/week-overview?start_date=YYYY-MM-DD
# Returns WeeklyLoad with 7-day summary starting from start_date (defaults to today)
```

**Implementation**:
1. Fetch Google Calendar events for 7 days
2. For each day, calculate:
   - `busy_hours`: Non-assignment events duration
   - `study_hours`: Assignment events duration
   - `total_events`: Count of all events
3. Aggregate into `WeeklyLoad` response
4. Cache for 1 hour

---

### 2. Enhanced Business Logic (Priority 1)

#### A. Planning Agent Integration
**File**: `app/services/planning_agent.py` (modify)

**Changes**:
1. Accept `user_preferences: Optional[DayPreferences]` parameter
2. Update `build_planning_prompt()` to include:
   ```
   **User Mood:** chill/normal/grind (affects intensity)
   **User Feeling:** overwhelmed/okay/on_top (affects load)
   ```
3. Adjust mode selection logic:
   - `mood=chill` or `feeling=overwhelmed` → bias toward OFF/LIGHT
   - `mood=grind` and `feeling=on_top` → bias toward NORMAL/HIGH
   - Default behavior if preferences not set
4. Append human-readable reason to `summary`:
   ```
   Planning mode: LIGHT (you selected 'chill' mood today)
   ```

---

#### B. Bus Logic Enhancement
**File**: `app/services/bus_service.py` (modify)

**Changes to `get_bus_suggestions_for_day()`**:
1. Calculate `minutes_until_leave` for each suggestion:
   ```python
   now = datetime.now(est)
   minutes = (bus.departure_time - now).total_seconds() / 60
   ```
2. Find `backup_bus`: Query next bus after primary suggestion
3. Return enhanced `BusSuggestion` objects with both fields

**Changes to `BusSuggestion.to_dict()`**:
1. Add `minutes_until_leave` and `backup_bus` to output

---

#### C. Assignment Grouping Logic
**File**: `app/services/assignment_grouper.py` (new)

**Function**: `group_assignments_for_display(assignments: List[Assignment], today: date) -> List[AssignmentGroup]`

**Logic**:
1. **Today's Focus** ✨: Due within 2 days OR priority=3
2. **This Week**: Due within 7 days
3. **Later**: Due >7 days

**Fields per assignment**:
- Standard assignment fields
- `due_in_days`: `(due_date - today).days`
- `progress`: `{ "sessions_today": count_from_schedule, "sessions_total": estimated_hours / 1.0 }`

---

#### D. Focus Assignments Extraction
**File**: `app/services/assignment_grouper.py`

**Function**: `extract_focus_assignments(assignments: List[Assignment], events: List[CalendarEvent]) -> List[FocusAssignment]`

**Logic**:
1. Filter top 3 most urgent (due soonest, priority highest)
2. Count `sessions_today` from scheduled blocks in `events`
3. Calculate `sessions_total` = `estimated_hours` / 1.0
4. Return `FocusAssignment` objects

---

#### E. Up Next Calculation
**File**: `app/services/up_next.py` (new)

**Function**: `calculate_up_next(events: List[CalendarEvent], free_blocks: List[FreeBlock]) -> Optional[UpNext]`

**Logic**:
1. Find next event/free block starting after `now`
2. Determine type:
   - `event_type="assignment"` → type="focus"
   - Regular event → type="event"
   - Free block → type="free"
3. Calculate `minutes_until` and format `start_label`
4. Return `UpNext` object

---

#### F. Tomorrow Preview
**File**: `app/services/tomorrow_preview.py` (new)

**Function**: `build_tomorrow_preview(db: Session, user_token: UserToken) -> TomorrowPreview`

**Logic**:
1. Fetch tomorrow's Google Calendar events
2. Calculate busy/study hours
3. Find first event time
4. Return `TomorrowPreview`

---

### 3. Day Plan Orchestrator Update (Priority 2)

**File**: `app/services/day_plan_orchestrator.py` (modify)

**Changes**:
1. Fetch `DayPreferences` from database
2. Pass preferences to planning agent
3. Call new helper services:
   - `group_assignments_for_display()`
   - `extract_focus_assignments()`
   - `calculate_up_next()`
   - `build_tomorrow_preview()`
4. Populate all optional fields in `DayPlanResponse`:
   ```python
   return DayPlanResponse(
       ...existing fields...,
       preferences=preferences_dict if preferences else None,
       assignment_groups=groups,
       focus_assignments=focus,
       up_next=up_next,
       tomorrow_preview=tomorrow,
   )
   ```

---

### 4. Calendar Endpoint Update (Priority 2)

**File**: `app/routes/calendar.py` (modify `/calendar/day-plan`)

**Changes**:
1. Orchestrator already returns enhanced response
2. No changes needed (backward compatible)
3. Optional v2 fields will be `None` for old clients

---

### 5. Frontend Implementation (Priority 3)

**File**: `frontend/app/dashboard/page.tsx` (major update)

#### A. New Components Needed
1. **MoodSelector**: Buttons for chill/normal/grind
2. **FeelingSelector**: Buttons for overwhelmed/okay/on_top
3. **FocusAssignments**: Cards showing today's focus with progress
4. **UpNextCard**: Next event/free time card
5. **TomorrowPreview**: Summary of tomorrow
6. **WeeklyLoadMeter**: 7-day bar chart
7. **Timeline**: Visual day timeline with events
8. **ThemeSelector**: Lavender/Sunrise/Matcha themes

#### B. API Integration
```typescript
// Fetch preferences
const prefs = await fetch('/api/preferences/day-preferences').then(r => r.json())

// Update preferences
await fetch('/api/preferences/day-preferences', {
  method: 'POST',
  body: JSON.stringify({ mood: 'chill', feeling: 'okay' })
})

// Fetch week overview
const weekLoad = await fetch('/api/calendar/week-overview').then(r => r.json())

// Block operations
await fetch(`/api/planner/blocks/${blockId}/skip-today`, { method: 'POST' })
await fetch(`/api/planner/blocks/${blockId}/move`, {
  method: 'POST',
  body: JSON.stringify({ new_start: '2025-11-07T14:00:00' })
})
```

#### C. Personalization
```tsx
const getGreeting = (hour: number) => {
  if (hour < 12) return "Good morning, Dippi 🌸"
  if (hour < 18) return "Good afternoon, Dippi 🌸"
  return "Good evening, Dippi 🌸"
}
```

#### D. Theme System
```tsx
const themes = {
  lavender: {
    primary: 'bg-purple-100',
    accent: 'border-purple-300',
    text: 'text-purple-900'
  },
  sunrise: {
    primary: 'bg-orange-100',
    accent: 'border-orange-300',
    text: 'text-orange-900'
  },
  matcha: {
    primary: 'bg-green-100',
    accent: 'border-green-300',
    text: 'text-green-900'
  }
}
```

---

## Implementation Order

### Phase 1: Backend Foundation (4-6 hours)
1. Preferences routes (30 min)
2. Planning agent integration (1 hour)
3. Bus logic enhancement (45 min)
4. Assignment grouping service (1 hour)
5. Up Next service (30 min)
6. Tomorrow preview service (30 min)
7. Week overview endpoint (45 min)

### Phase 2: Per-Block Operations (2-3 hours)
1. Skip route (45 min)
2. Move route (1 hour)
3. Duplicate route (45 min)

### Phase 3: Frontend (6-8 hours)
1. Mood/feeling selectors (1 hour)
2. Focus assignments cards (1.5 hours)
3. Up Next card (45 min)
4. Tomorrow preview (45 min)
5. Weekly load meter (1.5 hours)
6. Timeline component (2 hours)
7. Theme system (1 hour)

---

## Testing Checklist

### Backend
- [ ] Preferences CRUD operations
- [ ] Planning agent respects mood/feeling
- [ ] Bus suggestions include minutes_until_leave and backup
- [ ] Assignment grouping logic correct
- [ ] Up Next returns nearest event/free
- [ ] Tomorrow preview fetches correct data
- [ ] Week overview aggregates 7 days
- [ ] Block operations (skip/move/duplicate) work
- [ ] Cache invalidation triggers correctly

### Frontend
- [ ] Mood selector updates preferences
- [ ] Feeling selector updates preferences
- [ ] Focus assignments display with progress
- [ ] Up Next card shows correct event
- [ ] Tomorrow preview renders
- [ ] Weekly load meter visualizes correctly
- [ ] Timeline shows day schedule
- [ ] Theme switcher works
- [ ] Personalized greeting displays
- [ ] Block operations (skip/move/duplicate) work from UI

---

## Backward Compatibility

All v2 fields are **optional** in `DayPlanResponse`. Existing clients will:
- Receive `None` for new fields
- Continue working with `events`, `free_blocks`, `recommendations`

New clients can check for presence of v2 fields:
```typescript
if (response.preferences) {
  // Render mood/feeling
}
```

---

## Estimated Total Time: 12-17 hours

**Current Status**: ~20% complete (foundation)
**Remaining**: ~80% (routes, logic, frontend)

---

## Quick Start for Continuation

1. Start with **preferences routes**:
   ```bash
   # Create app/routes/preferences.py
   # Add to main.py: app.include_router(preferences.router)
   ```

2. Test preferences:
   ```bash
   curl -X POST http://localhost:8000/preferences/day-preferences \
     -H "Authorization: Bearer <token>" \
     -d '{"mood": "chill", "feeling": "okay"}'
   ```

3. Continue with planning agent integration, then bus logic, then frontend.

---

**Note**: This is a large feature. Consider breaking into smaller PRs or implementing in phases with feature flags.
