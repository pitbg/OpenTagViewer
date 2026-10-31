package dev.wander.android.opentagviewer.util.validate;

import android.webkit.URLUtil;

import java.net.URL;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;

@NoArgsConstructor(access = AccessLevel.PRIVATE)
public final class AnisetteUrlValidatorUtil {
    public static boolean isValidAnisetteUrl(final String urlInput) {
        if (!URLUtil.isHttpsUrl(urlInput) && !URLUtil.isHttpUrl(urlInput)) {
            return false;
        }
        try {
            var url = new URL(urlInput).toURI();

            // Standard servers use a base URL; the explicit path opts into
            // the experimental, identity-consistent macOS CoreADI bridge.
            var path = url.getPath();
            return path == null || path.isEmpty() || "/v3/get_headers".equals(path);

        } catch (Exception e) {
            return false;
        }
    }
}
