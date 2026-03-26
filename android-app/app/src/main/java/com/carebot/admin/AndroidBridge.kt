package com.carebot.admin

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import android.widget.Toast
import android.webkit.JavascriptInterface
import org.json.JSONArray
import org.json.JSONObject

class AdminDBHelper(context: Context) : SQLiteOpenHelper(context, "carebot_offline.db", null, 2) {
    override fun onCreate(db: SQLiteDatabase) {
        // Missions table
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS missions (
                id INTEGER PRIMARY KEY,
                type TEXT,
                reward TEXT,
                location TEXT,
                status INTEGER,
                winner_id INTEGER,
                created_at TEXT
            )
        """)
        
        // Battles table
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS battles (
                id INTEGER PRIMARY KEY,
                mission_id INTEGER,
                winner_id INTEGER,
                loser_id INTEGER,
                mission_type TEXT,
                location TEXT,
                result_timestamp TEXT,
                status TEXT,
                synced INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        
        // Pending syncs
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS pending_syncs (
                id INTEGER PRIMARY KEY,
                type TEXT,
                data TEXT,
                created_at TEXT,
                synced INTEGER DEFAULT 0
            )
        """)
    }
    
    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        if (oldVersion < 2) {
            try {
                db.execSQL("ALTER TABLE battles ADD COLUMN mission_type TEXT")
            } catch (_: Exception) { }
            try {
                db.execSQL("ALTER TABLE battles ADD COLUMN location TEXT")
            } catch (_: Exception) { }
            try {
                db.execSQL("ALTER TABLE battles ADD COLUMN result_timestamp TEXT")
            } catch (_: Exception) { }
        }
    }
}

class AndroidBridge(private val context: Context) {
    private val dbHelper = AdminDBHelper(context)
    
    @JavascriptInterface
    fun ping(): String {
        return "ok"
    }

    @JavascriptInterface
    fun showToast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }
    
    // ============== OFFLINE CACHE MANAGEMENT ==============
    
    @JavascriptInterface
    fun cacheMissions(missionsJson: String): String {
        return try {
            val db = dbHelper.writableDatabase
            val missions = JSONArray(missionsJson)
            
            db.beginTransaction()
            for (i in 0 until missions.length()) {
                val mission = missions.getJSONObject(i)
                val values = android.content.ContentValues().apply {
                    put("id", mission.getInt("id"))
                    put("type", mission.getString("type"))
                    put("reward", mission.getString("reward"))
                    put("location", mission.getString("location"))
                    put("status", mission.getInt("status"))
                    put("winner_id", mission.optInt("winner_id", -1))
                    put("created_at", mission.getString("created"))
                }
                db.insertWithOnConflict("missions", null, values, SQLiteDatabase.CONFLICT_REPLACE)
            }
            db.setTransactionSuccessful()
            db.endTransaction()
            
            JSONObject(mapOf("cached" to missions.length(), "status" to "ok")).toString()
        } catch (e: Exception) {
            JSONObject(mapOf("error" to e.message)).toString()
        }
    }
    
    @JavascriptInterface
    fun getCachedMissions(): String {
        return try {
            val db = dbHelper.readableDatabase
            val cursor = db.query(
                "missions",
                null,
                "status < 3",
                null,
                null,
                null,
                "created_at DESC"
            )
            
            val missions = JSONArray()
            while (cursor.moveToNext()) {
                missions.put(JSONObject(mapOf(
                    "id" to cursor.getInt(0),
                    "type" to cursor.getString(1),
                    "reward" to cursor.getString(2),
                    "location" to cursor.getString(3),
                    "status" to cursor.getInt(4)
                )))
            }
            cursor.close()
            
            JSONObject(mapOf("missions" to missions)).toString()
        } catch (e: Exception) {
            JSONObject(mapOf("error" to e.message)).toString()
        }
    }
    
    @JavascriptInterface
    fun savePendingBattleResult(resultJson: String): String {
        return try {
            val db = dbHelper.writableDatabase
            val result = JSONObject(resultJson)
            
            val values = android.content.ContentValues().apply {
                put("mission_id", result.getInt("mission_id"))
                put("winner_id", result.getInt("winner_id"))
                put("loser_id", result.getInt("loser_id"))
                put("mission_type", result.optString("mission_type", ""))
                put("location", result.optString("location", ""))
                put("result_timestamp", result.optString("timestamp", System.currentTimeMillis().toString()))
                put("status", "pending")
                put("synced", 0)
                put("created_at", System.currentTimeMillis().toString())
            }
            
            val id = db.insert("battles", null, values)
            
            JSONObject(mapOf("saved" to true, "id" to id)).toString()
        } catch (e: Exception) {
            JSONObject(mapOf("error" to e.message)).toString()
        }
    }
    
    // ============== SYNC MANAGEMENT ==============
    
    @JavascriptInterface
    fun getPendingBattles(): String {
        return try {
            val db = dbHelper.readableDatabase
            val cursor = db.query(
                "battles",
                null,
                "synced = 0",
                null,
                null,
                null,
                "created_at ASC"
            )
            
            val battles = JSONArray()
            while (cursor.moveToNext()) {
                battles.put(JSONObject(mapOf(
                    "id" to cursor.getInt(0),
                    "mission_id" to cursor.getInt(1),
                    "winner_id" to cursor.getInt(2),
                    "loser_id" to cursor.getInt(3),
                    "mission_type" to cursor.getString(4),
                    "location" to cursor.getString(5),
                    "timestamp" to cursor.getString(6)
                )))
            }
            cursor.close()
            
            JSONObject(mapOf("pending" to battles.length(), "battles" to battles)).toString()
        } catch (e: Exception) {
            JSONObject(mapOf("error" to e.message)).toString()
        }
    }
    
    @JavascriptInterface
    fun markBattlesAsSynced(battleIds: String): String {
        return try {
            val db = dbHelper.writableDatabase
            val ids = JSONArray(battleIds)
            
            db.beginTransaction()
            for (i in 0 until ids.length()) {
                val id = ids.getInt(i)
                val values = android.content.ContentValues().apply {
                    put("synced", 1)
                }
                db.update("battles", values, "id = ?", arrayOf(id.toString()))
            }
            db.setTransactionSuccessful()
            db.endTransaction()
            
            JSONObject(mapOf("synced" to ids.length())).toString()
        } catch (e: Exception) {
            JSONObject(mapOf("error" to e.message)).toString()
        }
    }
    
    @JavascriptInterface
    fun clearAllCache(): String {
        return try {
            val db = dbHelper.writableDatabase
            db.delete("missions", null, null)
            db.delete("battles", "synced = 1", null)
            
            JSONObject(mapOf("cleared" to true)).toString()
        } catch (e: Exception) {
            JSONObject(mapOf("error" to e.message)).toString()
        }
    }
}
