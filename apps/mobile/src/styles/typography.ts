/**
 * Copyright (C) 2026 Max Dietrich
 * Licensed under the GNU AGPLv3. See LICENSE in the project root for details.
 *
 * Re-exports typography from @hutts-tracking/shared — the single source of truth.
 * Platform-specific font variants (Regular, Medium, etc.) are derived here.
 */

import { TextStyle } from "react-native"
import { fontFamily } from "@hutts-tracking/shared"

export { fontSizes } from "@hutts-tracking/shared"

export const fonts: Record<string, Pick<TextStyle, "fontFamily">> = {
  regular: { fontFamily: `${fontFamily}-Regular` },
  medium: { fontFamily: `${fontFamily}-Medium` },
  semiBold: { fontFamily: `${fontFamily}-SemiBold` },
  bold: { fontFamily: `${fontFamily}-Bold` }
}
