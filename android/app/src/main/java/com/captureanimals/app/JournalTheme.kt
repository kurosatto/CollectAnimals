package com.captureanimals.app

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/*
 * The "Field Journal" look (2026-11, kuro picked it from four directions): a naturalist's
 * notebook. Leather top and tab bars with stitching, paper pages with faint ruled lines,
 * the habitat taped in like a photo, handwritten notes and ink stamps. Same look as the
 * website (index.html, "Field Journal look"). Fonts are OFL: Fraunces and Caveat (res/font).
 */

object Journal {
    val Leather = Color(0xFF5B3A22)
    val LeatherDark = Color(0xFF3F2715)
    val Brass = Color(0xFFC9A45A)
    val Cream = Color(0xFFF3E3BF)
    val CreamBright = Color(0xFFFFF3D6)
    val Card = Color(0xFFFFFAF0)          // a specimen card or photo border, same in dark mode
    val CardInk = Color(0xFF3A2C1C)
    val CardMuted = Color(0xFF7A6448)
    val Tape = Color(0xCCF0E1AA)
    val Stamp = Color(0xFF9B3B2A)
    val Hand = Color(0xFF2F4C6B)
    val HandDark = Color(0xFFA9C6E0)
}

val Fraunces = FontFamily(
    Font(R.font.fraunces_semibold, FontWeight.Normal),
    Font(R.font.fraunces_semibold, FontWeight.Medium),
    Font(R.font.fraunces_semibold, FontWeight.SemiBold),
    Font(R.font.fraunces_extrabold, FontWeight.Bold),
    Font(R.font.fraunces_extrabold, FontWeight.ExtraBold),
)
val Caveat = FontFamily(Font(R.font.caveat_semibold, FontWeight.Normal), Font(R.font.caveat_semibold, FontWeight.SemiBold))

private val LightJournal = lightColorScheme(
    primary = Color(0xFF4D6B3A), onPrimary = Color(0xFFFDF6E3),
    primaryContainer = Color(0xFFE3EBCF), onPrimaryContainer = Color(0xFF26361C),
    secondary = Journal.Leather, onSecondary = Journal.Cream,
    secondaryContainer = Color(0xFFEADBB8), onSecondaryContainer = Journal.CardInk,
    tertiary = Journal.Stamp,
    background = Color(0xFFEFE4C8), onBackground = Journal.CardInk,
    surface = Color(0xFFFBF5E6), onSurface = Journal.CardInk,
    surfaceVariant = Color(0xFFF1E7CF), onSurfaceVariant = Journal.CardMuted,
    surfaceContainer = Color(0xFFF6EEDA), surfaceContainerHigh = Color(0xFFF3EAD3),
    surfaceContainerHighest = Color(0xFFEFE4C8), surfaceContainerLow = Color(0xFFFBF5E6),
    surfaceContainerLowest = Journal.Card,
    outline = Color(0xFF9C8562), outlineVariant = Color(0xFFD9C9A3),
)

private val DarkJournal = darkColorScheme(
    primary = Color(0xFF9CBF7C), onPrimary = Color(0xFF1D1408),
    primaryContainer = Color(0xFF3B4E2C), onPrimaryContainer = Color(0xFFDDEBC8),
    secondary = Journal.Brass, onSecondary = Color(0xFF21140A),
    secondaryContainer = Color(0xFF4A3B28), onSecondaryContainer = Color(0xFFF0E4C8),
    tertiary = Color(0xFFE08A74),
    background = Color(0xFF211A12), onBackground = Color(0xFFF0E4C8),
    surface = Color(0xFF2C2318), onSurface = Color(0xFFF0E4C8),
    surfaceVariant = Color(0xFF3A2F21), onSurfaceVariant = Color(0xFFBBA57F),
    surfaceContainer = Color(0xFF2C2318), surfaceContainerHigh = Color(0xFF33291C),
    surfaceContainerHighest = Color(0xFF3A2F21), surfaceContainerLow = Color(0xFF272016),
    surfaceContainerLowest = Color(0xFF211A12),
    outline = Color(0xFF8C7656), outlineVariant = Color(0xFF4A3B28),
)

private fun journalType(): Typography {
    val base = Typography()
    fun TextStyle.f(weight: FontWeight? = null) = copy(fontFamily = Fraunces, fontWeight = weight ?: fontWeight)
    return Typography(
        displayLarge = base.displayLarge.f(FontWeight.ExtraBold), displayMedium = base.displayMedium.f(FontWeight.ExtraBold),
        displaySmall = base.displaySmall.f(FontWeight.ExtraBold), headlineLarge = base.headlineLarge.f(FontWeight.ExtraBold),
        headlineMedium = base.headlineMedium.f(FontWeight.ExtraBold), headlineSmall = base.headlineSmall.f(FontWeight.ExtraBold),
        titleLarge = base.titleLarge.f(FontWeight.ExtraBold), titleMedium = base.titleMedium.f(FontWeight.ExtraBold),
        titleSmall = base.titleSmall.f(FontWeight.Bold), bodyLarge = base.bodyLarge.f(), bodyMedium = base.bodyMedium.f(),
        bodySmall = base.bodySmall.f(), labelLarge = base.labelLarge.f(FontWeight.SemiBold),
        labelMedium = base.labelMedium.f(FontWeight.SemiBold), labelSmall = base.labelSmall.f(FontWeight.SemiBold),
    )
}

@Composable
fun JournalTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (isSystemInDarkTheme()) DarkJournal else LightJournal,
        typography = journalType(), content = content)
}

/** Handwriting, for notes and names on specimen cards. */
@Composable
fun handStyle(size: Int = 20): TextStyle = TextStyle(fontFamily = Caveat, fontSize = size.sp, lineHeight = (size * 1.1).sp,
    color = if (isSystemInDarkTheme()) Journal.HandDark else Journal.Hand)

/** Faint ruled lines, like notebook paper. */
fun Modifier.paperLines(color: Color): Modifier = drawBehind {
    val step = 32.dp.toPx()
    var y = step
    while (y < size.height) {
        drawLine(color, Offset(0f, y), Offset(size.width, y), strokeWidth = 1.dp.toPx())
        y += step
    }
}

/** Leather with a stitched border, for the top and tab bars. */
fun Modifier.leather(top: Boolean = true, bottom: Boolean = true): Modifier = background(Journal.Leather).drawBehind {
    val inset = 4.dp.toPx()
    val dash = 6.dp.toPx()
    fun stitch(y: Float) {
        var x = 0f
        while (x < size.width) {
            drawLine(Journal.Brass.copy(alpha = .55f), Offset(x, y), Offset(x + dash, y), strokeWidth = 1.5.dp.toPx())
            x += dash * 2
        }
    }
    if (top) stitch(inset)
    if (bottom) stitch(size.height - inset)
}

/** A photo taped into the journal: white border, a slight tilt, two strips of tape. */
@Composable
fun TapedPhoto(modifier: Modifier = Modifier, tilt: Float = -1.2f, content: @Composable () -> Unit) {
    Box(modifier.padding(top = 12.dp, start = 4.dp, end = 4.dp)) {
        Box(Modifier.rotate(tilt).shadow(6.dp).background(Journal.Card).padding(8.dp)) { content() }
        Box(Modifier.align(Alignment.TopStart).offset(x = 20.dp, y = (-10).dp).rotate(-7f).size(78.dp, 22.dp).background(Journal.Tape))
        Box(Modifier.align(Alignment.TopEnd).offset(x = (-20).dp, y = (-10).dp).rotate(6f).size(78.dp, 22.dp).background(Journal.Tape))
    }
}

/** A red ink stamp, like "Captured", set at an angle. */
@Composable
fun InkStamp(text: String, modifier: Modifier = Modifier, color: Color = MaterialTheme.colorScheme.tertiary) {
    Text(text.uppercase(), modifier.rotate(-4f).border(2.5.dp, color, RoundedCornerShape(4.dp)).padding(horizontal = 10.dp, vertical = 4.dp),
        color = color, fontFamily = Fraunces, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp, letterSpacing = 1.5.sp)
}
