package com.captureanimals.app

import android.content.Context
import android.net.Uri
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.SelectableDates
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TimePicker
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.material3.rememberTimePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.exifinterface.media.ExifInterface
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.time.Instant
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle

/**
 * When and where a capture was taken, as its owner sees it (the server's WhereWhenOut).
 * The time is the local wall time, as cameras record it.
 */
data class WhereWhen(
    val captureId: Int,
    val takenAt: LocalDateTime,
    // "photo" (its metadata), "upload" (no metadata: the upload time) or "edited".
    val timeSource: String,
    val latitude: Double?,
    val longitude: Double?,
    val place: String?,
    // "photo", "device", "edited", or null.
    val placeSource: String?,
) {
    companion object {
        fun parse(o: JSONObject?): WhereWhen? = o?.let {
            WhereWhen(it.getInt("capture_id"), LocalDateTime.parse(it.getString("taken_at")), it.getString("time_source"),
                it.optDoubleOrNull("latitude"), it.optDoubleOrNull("longitude"), it.optStringOrNull("place"),
                it.optStringOrNull("place_source"))
        }

        private fun JSONObject.optDoubleOrNull(k: String) = if (isNull(k)) null else optDouble(k)
    }
}

/** What the photo file itself says about when and where it was taken (EXIF). */
data class PhotoMeta(val latitude: Double?, val longitude: Double?, val takenAt: LocalDateTime?)

private val EXIF_TIME = DateTimeFormatter.ofPattern("yyyy:MM:dd HH:mm:ss")

/**
 * Reads the photo's EXIF time and GPS before it's shrunk for upload (which drops them).
 * Photos from the gallery picker usually have their location removed by Android.
 */
fun readPhotoMeta(context: Context, uri: Uri): PhotoMeta? = runCatching {
    context.contentResolver.openInputStream(uri)?.use { stream ->
        val exif = ExifInterface(stream)
        val latLong = exif.latLong
        val time = (exif.getAttribute(ExifInterface.TAG_DATETIME_ORIGINAL) ?: exif.getAttribute(ExifInterface.TAG_DATETIME))
            ?.let { runCatching { LocalDateTime.parse(it.trim().take(19), EXIF_TIME) }.getOrNull() }
        PhotoMeta(latLong?.get(0), latLong?.get(1), time)
    }
}.getOrNull()

private val SOURCE = mapOf("photo" to "from the photo", "device" to "from your phone",
    "upload" to "upload time", "edited" to "edited by you")

/** Saves a new time and place; returns an error message, or null when saved. */
typealias SaveWhereWhen = suspend (LocalDateTime, Pair<Double, Double>?) -> String?

/** The time and place lines with an "Edit time and place" button for the owner. */
@Composable
fun WhereWhenRow(ww: WhereWhen, parks: List<Park>, onSave: SaveWhereWhen) {
    var editing by remember { mutableStateOf(false) }
    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text("📅 " + ww.takenAt.format(DateTimeFormatter.ofLocalizedDateTime(FormatStyle.MEDIUM, FormatStyle.SHORT)) +
            (SOURCE[ww.timeSource]?.let { " · $it" } ?: ""), style = MaterialTheme.typography.bodyMedium)
        Text("📍 " + (ww.place ?: "No place saved") +
            (SOURCE[ww.placeSource]?.takeIf { ww.place != null }?.let { " · $it" } ?: ""),
            style = MaterialTheme.typography.bodyMedium)
        TextButton(onClick = { editing = true }, contentPadding = androidx.compose.foundation.layout.PaddingValues(0.dp)) {
            Text("Edit time and place")
        }
    }
    if (editing) WhereWhenDialog(ww, parks, onSave) { editing = false }
}

/**
 * Fix the date, time and place of a capture: the time can't be after the upload and the
 * place must be in the player's state (the server checks both). Places come from the
 * state's parks, where the phone is now, or no place.
 */
@OptIn(ExperimentalMaterial3Api::class, androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
@Composable
fun WhereWhenDialog(ww: WhereWhen, parks: List<Park>, onSave: SaveWhereWhen, onClose: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var date by remember { mutableStateOf(ww.takenAt.toLocalDate()) }
    var time by remember { mutableStateOf(ww.takenAt.toLocalTime()) }
    var place by remember { mutableStateOf(ww.latitude?.let { it to ww.longitude!! }) }
    var placeName by remember { mutableStateOf(ww.place) }
    var picking by remember { mutableStateOf<String?>(null) }  // "date", "time" or "park"
    var error by remember { mutableStateOf<String?>(null) }
    var saving by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onClose,
        title = { Text("When and where") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("When you took it", style = MaterialTheme.typography.labelLarge)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = { picking = "date" }) {
                        Text(date.format(DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM)))
                    }
                    OutlinedButton(onClick = { picking = "time" }) {
                        Text(time.format(DateTimeFormatter.ofLocalizedTime(FormatStyle.SHORT)))
                    }
                }
                Text("Where you took it", style = MaterialTheme.typography.labelLarge)
                Text("📍 " + (placeName ?: place?.let { "%.4f, %.4f".format(it.first, it.second) } ?: "No place"))
                androidx.compose.foundation.layout.FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    if (parks.isNotEmpty()) OutlinedButton(onClick = { picking = "park" }) { Text("Pick a park") }
                    if (hasLocationPermission(context)) OutlinedButton(onClick = {
                        lastLocation(context)?.let { place = it; placeName = "Where I am now" }
                            ?: run { error = "Couldn't get your location." }
                    }) { Text("Where I am now") }
                    TextButton(onClick = { place = null; placeName = null }) { Text("No place") }
                }
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        },
        confirmButton = {
            TextButton(enabled = !saving, onClick = {
                saving = true
                error = null
                scope.launch {
                    // Untouched, the photo's own seconds stay, so the time isn't marked as edited.
                    val picked = LocalDateTime.of(date, time)
                    val keep = picked.withSecond(0).withNano(0) == ww.takenAt.withSecond(0).withNano(0)
                    val err = onSave(if (keep) ww.takenAt else picked, place)
                    saving = false
                    if (err == null) onClose() else error = err
                }
            }) { Text("Save") }
        },
        dismissButton = { TextButton(onClick = onClose) { Text("Cancel") } },
    )

    when (picking) {
        "date" -> {
            val today = LocalDate.now()
            val state = rememberDatePickerState(
                initialSelectedDateMillis = date.atStartOfDay().toInstant(ZoneOffset.UTC).toEpochMilli(),
                selectableDates = object : SelectableDates {
                    override fun isSelectableDate(utcTimeMillis: Long) =
                        !Instant.ofEpochMilli(utcTimeMillis).atZone(ZoneOffset.UTC).toLocalDate().isAfter(today)
                    override fun isSelectableYear(year: Int) = year in 1990..today.year
                })
            DatePickerDialog(
                onDismissRequest = { picking = null },
                confirmButton = {
                    TextButton(onClick = {
                        state.selectedDateMillis?.let {
                            date = Instant.ofEpochMilli(it).atZone(ZoneOffset.UTC).toLocalDate()
                        }
                        picking = null
                    }) { Text("OK") }
                },
                dismissButton = { TextButton(onClick = { picking = null }) { Text("Cancel") } },
            ) { DatePicker(state) }
        }
        "time" -> {
            val state = rememberTimePickerState(time.hour, time.minute,
                is24Hour = android.text.format.DateFormat.is24HourFormat(context))
            AlertDialog(
                onDismissRequest = { picking = null },
                confirmButton = {
                    TextButton(onClick = { time = LocalTime.of(state.hour, state.minute); picking = null }) { Text("OK") }
                },
                dismissButton = { TextButton(onClick = { picking = null }) { Text("Cancel") } },
                text = { TimePicker(state) },
            )
        }
        "park" -> AlertDialog(
            onDismissRequest = { picking = null },
            title = { Text("Pick a park") },
            text = {
                LazyColumn(Modifier.heightIn(max = 400.dp)) {
                    items(parks.sortedBy { it.name }) { p ->
                        Text(p.name, Modifier.fillMaxWidth().clickable {
                            place = p.lat to p.lon; placeName = p.name; picking = null
                        }.padding(vertical = 10.dp))
                    }
                }
            },
            confirmButton = { TextButton(onClick = { picking = null }) { Text("Cancel") } },
        )
    }
}
