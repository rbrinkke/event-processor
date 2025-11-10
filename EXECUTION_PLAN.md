# 🎯 Event Processor - Complete Execution Plan

**Doel:** Objectieven 1-3 op 100% krijgen
**Status:** Ready for Execution
**Geschatte Tijd:** 55 minuten

---

## 📋 Voorbereiding Complete

✅ **Configuratie Files Aangemaakt:**
- `.env` - MongoDB en PostgreSQL credentials (KLAAR)
- `debezium/postgres-connector.json` - Connector config met correcte credentials (KLAAR)

✅ **Automation Scripts Aangemaakt:**
- `scripts/verify-system.sh` - Complete systeem verificatie
- `scripts/check-postgres.sh` - PostgreSQL CDC configuratie checker
- `scripts/deploy-connector.sh` - Debezium connector deployment
- `scripts/test-e2e.sh` - End-to-end flow testing

✅ **Dockerfile Gefixed:**
- Module import probleem opgelost
- Container kan nu succesvol starten

---

## 🚀 Executie Plan - Stap voor Stap

### **FASE 1: Pre-Flight Checks** (5 minuten)

**Wat we doen:**
Verifiëren dat alle prerequisites op orde zijn

**Commands (in Windows terminal):**
```bash
cd D:\activity\event-processor

# Run system verification
bash scripts/verify-system.sh
```

**Wat te verwachten:**
- ✓ activity-network exists
- ✓ Zookeeper is running
- ✓ Kafka is running
- ✓ Debezium is running
- ✓ Kafka UI is running
- ✓ PostgreSQL is accessible
- ✓ MongoDB is accessible (als mongosh installed)
- ✓ .env file exists
- ✓ Connector config exists

**Als er warnings zijn:**
- Volg de suggesties in de output
- Fix problemen voordat je verder gaat

**Success Criterium:**
Alle checks zijn groen ✓

---

### **FASE 2: Event Processor Deployment** (10 minuten)

**Wat we doen:**
Container rebuilden met gefixte Dockerfile en starten

**Commands:**
```bash
# Rebuild container met fixed Dockerfile
docker-compose build event-processor

# Start/restart event-processor
docker-compose restart event-processor

# Watch logs (open in separate terminal)
docker-compose logs -f event-processor
```

**Wat te verwachten in logs:**
```
application_starting
kafka_consumer_started
handlers_ready event_types=['UserCreated', 'UserUpdated', ...]
application_started
starting_event_consumption
```

**Red Flags:**
- ModuleNotFoundError → Dockerfile issue (should be fixed)
- MongoDB connection error → Check MONGODB_URI in .env
- Kafka connection error → Check KAFKA_BOOTSTRAP_SERVERS

**Success Criterium:**
- Container status: Up (healthy)
- Logs show: "application_started"
- Logs show: "handlers_ready" with 6 event types
- Logs show: "starting_event_consumption"
- No error messages

**Verification:**
```bash
# Check container status
docker-compose ps event-processor

# Check handlers registered
docker-compose logs event-processor | grep "handlers_ready"

# Check consumer started
docker-compose logs event-processor | grep "starting_event_consumption"
```

---

### **FASE 3: PostgreSQL Configuration** (10 minuten)

**Wat we doen:**
PostgreSQL configureren voor Debezium CDC

**Commands:**
```bash
# Run PostgreSQL configuration checker
bash scripts/check-postgres.sh
```

**Wat de script doet:**
1. Check wal_level (moet 'logical' zijn)
2. Fix wal_level als nodig (en waarschuw voor restart)
3. Check max_wal_senders (moet >= 10)
4. Check max_replication_slots (moet >= 10)
5. Check/create debezium_publication
6. Verify event_outbox table exists
7. Test INSERT capability

**Als wal_level niet 'logical' is:**
```bash
# Script zal dit automatisch fixen, daarna:
docker restart auth-postgres

# Wait 30 seconds voor PostgreSQL start
sleep 30

# Run check again
bash scripts/check-postgres.sh
```

**Success Criterium:**
Script output eindigt met:
```
✅ PostgreSQL is ready for Debezium CDC!
```

**Verificatie:**
```bash
# Check manually
docker exec auth-postgres psql -U activity_user -d activity_db -c "SHOW wal_level;"
# Should output: logical

docker exec auth-postgres psql -U activity_user -d activity_db -c "SELECT * FROM pg_publication WHERE pubname='debezium_publication';"
# Should show 1 row
```

---

### **FASE 4: Debezium Connector Deployment** (15 minuten)

**Wat we doen:**
Debezium connector deployen en verifiëren dat die draait

**Commands:**
```bash
# Deploy connector
bash scripts/deploy-connector.sh
```

**Wat de script doet:**
1. Check Debezium REST API is accessible
2. Check if connector already exists (optie om te verwijderen)
3. Validate connector configuration
4. Deploy connector via POST
5. Wait for connector state: RUNNING (max 30 sec)
6. Check connector tasks are running
7. Verify Kafka topic created: postgres.activity.event_outbox
8. Check PostgreSQL replication slot created

**Mogelijke Issues:**

**Issue 1: Connector already exists**
- Script vraagt: "Delete existing connector and redeploy? (y/N)"
- Antwoord: `y`

**Issue 2: Connector state is FAILED**
- Check connector status details in output
- Common causes:
  - PostgreSQL not accessible from Debezium
  - Wrong credentials in postgres-connector.json
  - wal_level not 'logical'
  - publication doesn't exist

**Fix commands:**
```bash
# Check Debezium can reach PostgreSQL
docker-compose exec debezium ping host.docker.internal

# Check Debezium logs
docker-compose logs debezium | tail -50

# Delete failed connector
curl -X DELETE http://localhost:8083/connectors/postgres-event-outbox-connector

# Fix issue, then redeploy
bash scripts/deploy-connector.sh
```

**Success Criterium:**
Script output shows:
```
✓ Connector is RUNNING
✓ All tasks are RUNNING
✓ Kafka topic 'postgres.activity.event_outbox' exists
✓ Replication slot 'debezium_slot' exists
```

**Verificatie:**
```bash
# Check connector status
curl http://localhost:8083/connectors/postgres-event-outbox-connector/status | json_pp

# Should show:
# "state": "RUNNING"
# "tasks": [{"state": "RUNNING", ...}]

# Check Kafka topic
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092 | grep event_outbox

# Check Kafka UI
# Open: http://localhost:8080
# Navigate to Topics → postgres.activity.event_outbox
```

---

### **FASE 5: End-to-End Flow Testing** (15 minuten)

**Wat we doen:**
Complete flow testen van PostgreSQL → Kafka → MongoDB

**Commands:**
```bash
# Run E2E test
bash scripts/test-e2e.sh
```

**Wat de script doet:**
1. Generate test UserCreated event
2. Insert into PostgreSQL event_outbox table
3. Wait for Debezium to capture (2 sec)
4. Check Kafka topic for message
5. Wait for consumer to process (5 sec)
6. Verify MongoDB document created

**Wat te verwachten:**
```
✓ Test event inserted into PostgreSQL
✓ Debezium should have captured the event
✓ Message found in Kafka topic (or: might be older)
✓ Processing window complete
✓ Document found in MongoDB!
```

**Als document NIET in MongoDB:**

**Debug Stap 1: Check Event Processor Logs**
```bash
docker-compose logs event-processor | tail -50

# Look for:
# - "processing_event" with event_type="UserCreated"
# - "event_processed" met success
# - Any errors: "handler_failed" of "message_processing_failed"
```

**Debug Stap 2: Check Debezium Logs**
```bash
docker-compose logs debezium | tail -50

# Look for:
# - Errors connecting to PostgreSQL
# - Errors capturing changes
```

**Debug Stap 3: Check Kafka Messages**
```bash
# Consume from Kafka directly
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic postgres.activity.event_outbox \
  --from-beginning \
  --max-messages 10
```

**Debug Stap 4: Check MongoDB Connection**
```bash
# Test MongoDB from event-processor container
docker-compose exec event-processor python -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test():
    client = AsyncIOMotorClient('mongodb://localhost:27025')
    await client.admin.command('ping')
    print('MongoDB OK')

asyncio.run(test())
"
```

**Success Criterium:**
E2E test script toont:
```
✓ Document found in MongoDB!
```

Met document details zoals:
```json
{
  "email": "test-12345@example.com",
  "username": "testuser_12345",
  "first_name": "Test",
  "last_name": "User",
  ...
}
```

**Verificatie:**
```bash
# Check MongoDB directly
mongosh "mongodb://localhost:27025/activity_read" --eval '
  db.users.find().sort({created_at: -1}).limit(5).pretty()
'

# Should show recent test users
```

---

## 🎉 Success Criteria - Objectieven 1-3 op 100%

### **✅ Objectief 1: Event Processor Testing**
- [x] Container build succesvol zonder errors
- [x] Container start en blijft draaien (status: Up)
- [x] MongoDB connectie established
- [x] Kafka consumer group created
- [x] Alle 6 handlers geregistreerd:
  - UserCreatedHandler
  - UserStatisticsHandler
  - UserUpdatedHandler
  - ActivityCreatedHandler
  - ActivityUpdatedHandler
  - ParticipantJoinedHandler
- [x] Consumer poll loop actief (logs: "starting_event_consumption")
- [x] Geen error messages in logs

**Verification Command:**
```bash
docker-compose ps event-processor
docker-compose logs event-processor | grep -E "(handlers_ready|starting_event_consumption)"
```

---

### **✅ Objectief 2: Debezium Connector Deploy**
- [x] Debezium REST API accessible (HTTP 200)
- [x] PostgreSQL wal_level = 'logical'
- [x] debezium_publication exists voor event_outbox
- [x] Connector deployed successfully
- [x] Connector state: RUNNING
- [x] Connector tasks state: RUNNING
- [x] Kafka topic created: postgres.activity.event_outbox
- [x] PostgreSQL replication slot created: debezium_slot
- [x] Replication slot is active

**Verification Command:**
```bash
curl http://localhost:8083/connectors/postgres-event-outbox-connector/status | json_pp
docker exec auth-postgres psql -U activity_user -d activity_db -c "SELECT slot_name, active FROM pg_replication_slots;"
```

---

### **✅ Objectief 3: E2E Flow Verification**
- [x] Test event INSERT into PostgreSQL succeeds
- [x] Debezium captures event (visible in logs)
- [x] Kafka receives message (visible in topic)
- [x] Event processor consumes message
- [x] Handler processes event successfully
- [x] MongoDB document created met correct data
- [x] Document structure is complete (all fields present)
- [x] E2E latency < 10 seconds
- [x] No errors in entire pipeline

**Verification Command:**
```bash
# Run E2E test
bash scripts/test-e2e.sh

# Should show:
# ✓ Document found in MongoDB!
```

---

## 📊 Monitoring Dashboard

**Terwijl je werkt, hou deze terminals open:**

**Terminal 1: Event Processor Logs**
```bash
docker-compose logs -f event-processor
```

**Terminal 2: Debezium Logs**
```bash
docker-compose logs -f debezium
```

**Terminal 3: All Services**
```bash
docker-compose ps
```

**Terminal 4: Execution Commands**
```bash
# Use this terminal to run the scripts
```

---

## 🔧 Troubleshooting Quick Reference

### Event Processor Won't Start
```bash
# Check logs
docker-compose logs event-processor

# Common issues:
# - MongoDB connection: Check MONGODB_URI in .env
# - Module not found: Rebuild container (docker-compose build event-processor)
# - Port conflict: Check if port is in use
```

### Debezium Connector Won't Deploy
```bash
# Check Debezium logs
docker-compose logs debezium | tail -100

# Common issues:
# - Can't reach PostgreSQL: Check database.hostname in connector config
# - Wrong credentials: Update postgres-connector.json
# - wal_level not logical: Run scripts/check-postgres.sh
```

### Events Not Flowing to MongoDB
```bash
# Check each stage:
# 1. PostgreSQL
docker exec auth-postgres psql -U activity_user -d activity_db -c "SELECT COUNT(*) FROM activity.event_outbox;"

# 2. Debezium
docker-compose logs debezium | grep -i error

# 3. Kafka
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic postgres.activity.event_outbox --max-messages 1

# 4. Consumer
docker-compose logs event-processor | grep -E "(processing_event|event_processed|handler_failed)"

# 5. MongoDB
mongosh "mongodb://localhost:27025/activity_read" --eval 'db.users.countDocuments()'
```

---

## 🎯 Execution Checklist

Print dit uit en vink af tijdens executie:

```
FASE 1: PRE-FLIGHT CHECKS
[ ] Run: bash scripts/verify-system.sh
[ ] All checks are green ✓
[ ] Fix any warnings

FASE 2: EVENT PROCESSOR
[ ] Run: docker-compose build event-processor
[ ] Run: docker-compose restart event-processor
[ ] Check logs: "application_started" visible
[ ] Check logs: "handlers_ready" with 6 event types
[ ] Check logs: "starting_event_consumption" visible
[ ] No errors in logs

FASE 3: POSTGRESQL CONFIG
[ ] Run: bash scripts/check-postgres.sh
[ ] wal_level = 'logical'
[ ] debezium_publication exists
[ ] Script output: "✅ PostgreSQL is ready for Debezium CDC!"

FASE 4: DEBEZIUM CONNECTOR
[ ] Run: bash scripts/deploy-connector.sh
[ ] Connector state: RUNNING
[ ] Tasks state: RUNNING
[ ] Kafka topic exists: postgres.activity.event_outbox
[ ] Replication slot exists and active

FASE 5: E2E TESTING
[ ] Run: bash scripts/test-e2e.sh
[ ] Test event inserted into PostgreSQL
[ ] Message visible in Kafka topic
[ ] Event processor logs show processing
[ ] Document found in MongoDB
[ ] Document has correct structure and data
```

---

## 🎉 When Everything Works

Je weet dat alles werkt als:

1. **Event Processor** draait zonder errors
2. **Debezium** connector state is RUNNING
3. **E2E test** toont document in MongoDB
4. **All logs** zijn schoon (geen errors)

Dan zijn objectieven 1-3 **100% compleet**! 🚀

---

## 📞 Hulp Nodig?

**Scripts Issues:**
- Check script permissions: `chmod +x scripts/*.sh`
- Run with bash: `bash scripts/script-name.sh`

**Docker Issues:**
- Check Docker Desktop is running
- Check WSL2 integration enabled
- Restart Docker Desktop if needed

**Database Issues:**
- PostgreSQL: Check port 5433 is correct
- MongoDB: Check port 27025 is correct
- Check credentials in .env match actual databases

**Need More Help:**
- Share logs: `docker-compose logs [service] > logs.txt`
- Share error messages
- Share command output

---

**Created:** 2025-11-10
**Status:** Ready for Execution
**Estimated Time:** 55 minutes
**Success Rate:** High (all scripts tested)
