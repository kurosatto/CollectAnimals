package com.captureanimals.app

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LocalTextStyle
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
import androidx.compose.ui.layout.layout
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/*
 * The "Field Journal" look (2026-11, kuro picked it from four directions): a naturalist's
 * notebook. Leather top and tab bars with stitching, paper pages with faint ruled lines,
 * ink stamps. Same look as the website (index.html, "Field Journal look" and "Phone fit").
 * 2026-11-04 (kuro): the habitat fills the screen width with no photo frame, and no italic
 * or handwritten fonts: Pixelify Sans (pixel, for headings, buttons, labels) and Space
 * Grotesk (reading text), both OFL (res/font).
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

/** The pixel font: headings, buttons, tabs, labels and names. */
val PixelFont = FontFamily(
    Font(R.font.pixelify_semibold, FontWeight.Normal),
    Font(R.font.pixelify_semibold, FontWeight.Medium),
    Font(R.font.pixelify_semibold, FontWeight.SemiBold),
    Font(R.font.pixelify_bold, FontWeight.Bold),
    Font(R.font.pixelify_bold, FontWeight.ExtraBold),
)
/** Reading text. */
val TextFont = FontFamily(
    Font(R.font.spacegrotesk_medium, FontWeight.Normal),
    Font(R.font.spacegrotesk_medium, FontWeight.Medium),
    Font(R.font.spacegrotesk_bold, FontWeight.SemiBold),
    Font(R.font.spacegrotesk_bold, FontWeight.Bold),
)

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
    // Pixel headings, buttons and labels; a little smaller than Material's defaults so more
    // fits on a phone.
    fun TextStyle.px(size: Int, weight: FontWeight = FontWeight.Bold) =
        copy(fontFamily = PixelFont, fontWeight = weight, fontSize = size.sp, lineHeight = (size * 1.25).sp)
    fun TextStyle.tx(size: Int) = copy(fontFamily = TextFont, fontSize = size.sp, lineHeight = (size * 1.4).sp)
    return Typography(
        displayLarge = base.displayLarge.px(44), displayMedium = base.displayMedium.px(36),
        displaySmall = base.displaySmall.px(30), headlineLarge = base.headlineLarge.px(26),
        headlineMedium = base.headlineMedium.px(23), headlineSmall = base.headlineSmall.px(20),
        titleLarge = base.titleLarge.px(19), titleMedium = base.titleMedium.px(16),
        titleSmall = base.titleSmall.px(14), bodyLarge = base.bodyLarge.tx(15), bodyMedium = base.bodyMedium.tx(14),
        bodySmall = base.bodySmall.tx(12), labelLarge = base.labelLarge.px(14, FontWeight.SemiBold),
        labelMedium = base.labelMedium.px(12, FontWeight.SemiBold), labelSmall = base.labelSmall.px(11, FontWeight.SemiBold),
    )
}

@Composable
fun JournalTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (isSystemInDarkTheme()) DarkJournal else LightJournal,
        typography = journalType(), content = content)
}

/** Notes and names on specimen cards, in the pixel font (was handwriting until 2026-11-04). */
@Composable
fun handStyle(size: Int = 14): TextStyle = TextStyle(fontFamily = PixelFont, fontWeight = FontWeight.Medium,
    fontSize = size.sp, lineHeight = (size * 1.25).sp, color = if (isSystemInDarkTheme()) Journal.HandDark else Journal.Hand)

/** A 16 px pixel icon (tools/make_ui_icons.py: pin, coin, lock, warn, chat...) in front of
 *  a line of text, in place of an emoji. */
@Composable
fun IconText(icon: String, text: String, modifier: Modifier = Modifier, style: TextStyle = LocalTextStyle.current,
             color: Color = Color.Unspecified) {
    Row(modifier, verticalAlignment = Alignment.CenterVertically) {
        TabIcon(if (icon.startsWith("tab_")) "ui_$icon" else "ui_ic_$icon", Modifier.size(16.dp))
        Spacer(Modifier.width(5.dp))
        Text(text, style = style, color = color)
    }
}

/** Lets a child reach past its parent's side padding, so the habitat can fill the screen width. */
fun Modifier.bleed(side: Dp): Modifier = layout { m, c ->
    val extra = (side * 2).roundToPx()
    val w = c.maxWidth + extra
    val p = m.measure(c.copy(minWidth = w, maxWidth = w))
    layout(c.maxWidth, p.height) { p.place(-side.roundToPx(), 0) }
}

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

/** A red ink stamp, like "Captured", set at an angle. */
@Composable
fun InkStamp(text: String, modifier: Modifier = Modifier, color: Color = MaterialTheme.colorScheme.tertiary) {
    Text(text.uppercase(), modifier.rotate(-4f).border(2.5.dp, color, RoundedCornerShape(4.dp)).padding(horizontal = 10.dp, vertical = 4.dp),
        color = color, fontFamily = PixelFont, fontWeight = FontWeight.Bold, fontSize = 14.sp, letterSpacing = 1.5.sp)
}

/** Leather for the tab strip down the side of a phone held sideways: stitching along its inner edge. */
fun Modifier.leatherSide(): Modifier = background(Journal.Leather).drawBehind {
    val x = size.width - 4.dp.toPx()
    val dash = 6.dp.toPx()
    var y = 0f
    while (y < size.height) {
        drawLine(Journal.Brass.copy(alpha = .55f), Offset(x, y), Offset(x, y + dash), strokeWidth = 1.5.dp.toPx())
        y += dash * 2
    }
}

/**
 * A phone held sideways: wider than tall and short (tablets stay as they are). Such a
 * screen gets the tabs down the side and pictures sized to its height (kuro, 2026-11-13).
 */
@Composable
fun isSideways(): Boolean {
    val c = androidx.compose.ui.platform.LocalConfiguration.current
    return c.screenWidthDp > c.screenHeightDp && c.screenHeightDp < 520
}

/**
 * How wide the habitat can be so its whole scene fits in [height] (the scene plus its
 * one-line note under it). habitat.js draws the wide 480x270 scene from 440 px wide and
 * the narrow 320x270 one below that.
 */
fun habitatWidthFor(height: Dp): Dp {
    val scene = (height - 36.dp).coerceAtLeast(120.dp)
    val wide = scene * (16f / 9f)
    return if (wide >= 440.dp) wide else scene * (32f / 27f)
}

/** Fills the width, keeping [aspect] (width / height), but no taller than [share] of a sideways screen. */
@Composable
fun Modifier.fitSideways(aspect: Float, share: Float = .75f): Modifier {
    val h = androidx.compose.ui.platform.LocalConfiguration.current.screenHeightDp * share
    return this.widthIn(max = (h * aspect).dp).fillMaxWidth().aspectRatio(aspect)
}

/** A list inside a pop-up: up to 360 dp, less on a short (sideways) screen so the buttons still show. */
@Composable
fun dialogListMax(): Dp =
    minOf(360, (androidx.compose.ui.platform.LocalConfiguration.current.screenHeightDp * .45f).toInt()).dp

/** On a sideways phone, a habitat in a pop-up no wider than lets it fit in [share] of the screen's height. */
@Composable
fun sidewaysHabitat(share: Float): Modifier = if (!isSideways()) Modifier else Modifier.widthIn(
    max = habitatWidthFor((androidx.compose.ui.platform.LocalConfiguration.current.screenHeightDp * share).dp))
