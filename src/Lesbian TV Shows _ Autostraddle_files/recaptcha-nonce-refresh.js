/**
 * reCAPTCHA Nonce Refresh for Cached Pages
 *
 * This script handles the refreshing of WordPress nonces for Gravity Forms
 * reCAPTCHA v3 validation when pages are served from cache (WPVIP).
 *
 * The Problem:
 * - WPVIP aggressively caches pages for performance
 * - WordPress nonces embedded in the HTML become stale (nonces expire)
 * - Gravity Forms reCAPTCHA uses these nonces for server-side token verification
 * - Stale nonces cause reCAPTCHA validation to fail
 *
 * The Solution:
 * - Hook into Gravity Forms' async filter system (gform/submission/pre_submission)
 * - Fetch fresh nonces via AJAX before form submission proceeds
 * - Update the global reCAPTCHA strings object with fresh values
 * - AJAX endpoint is configured to bypass all caching layers
 *
 * @package AS_GF_Recaptcha_Cache_Fix
 * @since 1.0.0
 */

(function($) {
    'use strict';

    /**
     * RecaptchaNonceRefresh object
     *
     * Manages the nonce refresh lifecycle for Gravity Forms
     */
    var RecaptchaNonceRefresh = {

        /**
         * Configuration options
         */
        config: {
            // Refresh nonces on page load (recommended for long page sessions)
            refreshOnLoad: true,
            // Timeout for AJAX requests (ms)
            ajaxTimeout: 10000,
            // Retry failed requests
            retryOnFailure: true,
            // Maximum retry attempts
            maxRetries: 2,
            // Delay between retries (ms)
            retryDelay: 1000
        },

        /**
         * State tracking
         */
        state: {
            isRefreshing: false,
            lastRefreshTime: 0,
            refreshCount: 0,
            isGformFilterInitialized: false,
            retryCount: 0,
            pendingRefreshPromise: null
        },

        /**
         * Minimum time between refreshes (ms) to prevent excessive requests
         */
        MIN_REFRESH_INTERVAL: 5000,

        /**
         * Initialize the nonce refresh functionality
         */
        init: function() {
            var self = this;

            // Wait for document ready
            $(document).ready(function() {
                self.log('Initializing reCAPTCHA nonce refresh v1.1.0');
                
                // Refresh on page load to get fresh nonces immediately
                if (self.config.refreshOnLoad) {
                    self.refreshNonce();
                }

                // Initialize Gravity Forms filter integration
                self.initGformFilters();
            });

            // Listen for page visibility changes (refresh when tab becomes active)
            document.addEventListener('visibilitychange', function() {
                if (document.visibilityState === 'visible') {
                    var timeSinceLastRefresh = Date.now() - self.state.lastRefreshTime;
                    // Refresh if more than 2 minutes have passed
                    if (timeSinceLastRefresh > 120000) {
                        self.log('Tab became visible, refreshing stale nonces');
                        self.refreshNonce();
                    }
                }
            });
        },

        /**
         * Initialize Gravity Forms async filter integration
         * 
         * This hooks into GF's native submission flow rather than hijacking the submit event.
         * The filter runs BEFORE reCAPTCHA token generation, ensuring fresh nonces are in place.
         */
        initGformFilters: function() {
            var self = this;

            // Wait for gform to be available
            if (typeof window.gform === 'undefined' || typeof window.gform.utils === 'undefined') {
                // Retry after a short delay if gform isn't ready yet
                setTimeout(function() {
                    self.initGformFilters();
                }, 100);
                return;
            }

            // Only initialize once
            if (this.state.isGformFilterInitialized) {
                return;
            }
            this.state.isGformFilterInitialized = true;

            this.log('Registering Gravity Forms async filters');

            // Hook into pre-submission filter with high priority (runs early)
            // Priority 1 ensures we run before reCAPTCHA token generation
            window.gform.utils.addAsyncFilter('gform/submission/pre_submission', function(data) {
                return self.handlePreSubmission(data);
            }, 1);

            // Also hook into AJAX validation for inline validation
            window.gform.utils.addAsyncFilter('gform/ajax/pre_ajax_validation', function(data) {
                return self.handlePreSubmission(data);
            }, 1);

            this.log('Gravity Forms filters registered successfully');
        },

        /**
         * Handle pre-submission filter
         * 
         * This is called by Gravity Forms before form submission proceeds.
         * We refresh the nonce here and return a Promise that resolves when done.
         * 
         * @param {object} data The submission data from GF
         * @return {Promise} Promise that resolves with the data object
         */
        handlePreSubmission: function(data) {
            var self = this;

            // Check if submission is being aborted
            if (data.abort) {
                self.log('Submission aborted, skipping nonce refresh');
                return Promise.resolve(data);
            }

            // Check if we recently refreshed
            var timeSinceRefresh = Date.now() - this.state.lastRefreshTime;
            if (timeSinceRefresh < this.MIN_REFRESH_INTERVAL && this.state.refreshCount > 0) {
                self.log('Nonce recently refreshed (' + Math.round(timeSinceRefresh/1000) + 's ago), allowing submission');
                return Promise.resolve(data);
            }

            self.log('Pre-submission: refreshing nonce before form submission...');

            // Return a Promise that resolves after nonce refresh
            return new Promise(function(resolve) {
                self.refreshNonce(function(success) {
                    if (success) {
                        self.log('Nonce refreshed, proceeding with submission');
                    } else {
                        self.log('Nonce refresh failed, proceeding anyway (nonce might still be valid)', 'warn');
                    }
                    // Always resolve - don't block submission on refresh failure
                    resolve(data);
                });
            });
        },

        /**
         * Refresh the reCAPTCHA nonce via AJAX
         *
         * @param {function} callback Optional callback function(success)
         * @return {Promise|void} Returns promise if no callback provided
         */
        refreshNonce: function(callback) {
            var self = this;

            // If there's already a pending refresh, wait for it
            if (this.state.pendingRefreshPromise) {
                this.log('Refresh already in progress, waiting...');
                if (typeof callback === 'function') {
                    this.state.pendingRefreshPromise.then(function() {
                        callback(true);
                    }).catch(function() {
                        callback(false);
                    });
                    return;
                }
                return this.state.pendingRefreshPromise;
            }

            // Throttle requests
            var timeSinceLastRefresh = Date.now() - this.state.lastRefreshTime;
            if (timeSinceLastRefresh < this.MIN_REFRESH_INTERVAL && this.state.refreshCount > 0) {
                this.log('Throttling refresh request (too frequent)');
                if (typeof callback === 'function') {
                    callback(true); // Consider it success since we recently refreshed
                }
                return Promise.resolve(true);
            }

            this.state.isRefreshing = true;
            this.log('Sending nonce refresh request...');

            // Create the refresh promise
            this.state.pendingRefreshPromise = new Promise(function(resolve, reject) {
                $.ajax({
                    url: asGfRecaptchaFix.ajaxurl,
                    type: 'POST',
                    data: {
                        action: 'as_gf_recaptcha_refresh_nonce',
                        security: asGfRecaptchaFix.security
                    },
                    cache: false,
                    timeout: self.config.ajaxTimeout,
                    // Add cache-busting headers
                    headers: {
                        'Cache-Control': 'no-cache, no-store',
                        'Pragma': 'no-cache'
                    },
                    success: function(response) {
                        self.state.isRefreshing = false;
                        self.state.pendingRefreshPromise = null;
                        self.state.retryCount = 0;

                        if (response.success && response.data) {
                            self.updateNonces(response.data);
                            self.state.lastRefreshTime = Date.now();
                            self.state.refreshCount++;

                            self.log('Nonce refreshed successfully (count: ' + self.state.refreshCount + ')');

                            // Update security nonce for next request
                            if (response.data.security) {
                                asGfRecaptchaFix.security = response.data.security;
                            }

                            resolve(true);
                            if (typeof callback === 'function') {
                                callback(true);
                            }
                        } else {
                            self.log('Nonce refresh returned unexpected response', 'error');
                            self.handleRefreshError(callback, resolve, reject);
                        }
                    },
                    error: function(xhr, status, error) {
                        self.state.isRefreshing = false;
                        self.state.pendingRefreshPromise = null;
                        self.log('AJAX error: ' + error, 'error');
                        self.handleRefreshError(callback, resolve, reject);
                    }
                });
            });

            return this.state.pendingRefreshPromise;
        },

        /**
         * Handle refresh errors with optional retry
         *
         * @param {function} callback Callback function
         * @param {function} resolve Promise resolve function
         * @param {function} reject Promise reject function
         */
        handleRefreshError: function(callback, resolve, reject) {
            var self = this;

            if (this.config.retryOnFailure && this.state.retryCount < this.config.maxRetries) {
                this.state.retryCount++;
                this.log('Retrying nonce refresh (attempt ' + this.state.retryCount + ')');

                setTimeout(function() {
                    self.refreshNonce(callback).then(resolve).catch(reject);
                }, this.config.retryDelay);
            } else {
                this.state.retryCount = 0;
                if (typeof callback === 'function') {
                    callback(false);
                }
                // Resolve instead of reject - we don't want to block form submission
                if (typeof resolve === 'function') {
                    resolve(false);
                }
            }
        },

        /**
         * Update the nonces in the global reCAPTCHA strings object
         *
         * @param {object} data The fresh nonce data from the server
         */
        updateNonces: function(data) {
            // Update Gravity Forms reCAPTCHA strings if they exist
            if (typeof gforms_recaptcha_recaptcha_strings !== 'undefined') {
                if (data.recaptcha_nonce) {
                    gforms_recaptcha_recaptcha_strings.nonce = data.recaptcha_nonce;
                    this.log('Updated gforms_recaptcha_recaptcha_strings.nonce');
                }
                if (data.site_key) {
                    gforms_recaptcha_recaptcha_strings.site_key = data.site_key;
                }
                if (data.ajaxurl) {
                    gforms_recaptcha_recaptcha_strings.ajaxurl = data.ajaxurl;
                }
            } else {
                this.log('gforms_recaptcha_recaptcha_strings not found (form may not have reCAPTCHA)', 'warn');
            }

            // Dispatch event for other scripts that might need fresh nonces
            $(document).trigger('as_gf_recaptcha_nonces_refreshed', [data]);
        },

        /**
         * Log messages to console (only in debug mode)
         *
         * @param {string} message The message to log
         * @param {string} level The log level (log, warn, error)
         */
        log: function(message, level) {
            if (!asGfRecaptchaFix.debug) {
                return;
            }

            level = level || 'log';
            var prefix = '[AS GF reCAPTCHA Fix]';

            switch (level) {
                case 'warn':
                    console.warn(prefix, message);
                    break;
                case 'error':
                    console.error(prefix, message);
                    break;
                default:
                    console.log(prefix, message);
            }
        }
    };

    // Initialize
    RecaptchaNonceRefresh.init();

    // Expose for debugging
    window.ASGFRecaptchaFix = RecaptchaNonceRefresh;

})(jQuery);
