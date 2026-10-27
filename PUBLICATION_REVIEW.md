# Publication review

This package is a conservative public-code extraction based on deployed commit `fb036a067abd84359285579858d4099df45c3be6`. It is not the production deployment.

## Included

- The forecasting, player rating, feature generation, fitting, training and evaluation algorithms, plus historical protocol definitions.
- Original project code offered under MIT, with pinned dependency versions. Dependencies are installed separately and retain their own licenses.
- Fictional teams, players, model state and clearly labeled unfitted coefficients; synthetic demo and unit tests.
- A required user-supplied list of event IDs to exclude during optional winner training; no original provider event IDs are hard-coded.

## Excluded

Real fitted coefficients, numerical historical evaluation results, original data, raw reports, historical game records, per-game predictions, databases, live production state, saved forecasts, network ingestion, credentials, internal endpoints, access-control and administrative code, and scheduled updater code. No third-party dataset is included. The original production evaluation is not reproducible from the package alone.

ESPN was the historical schedule and box-score source. ESPN directs users to Disney's terms, which restrict certain automated extraction, use and transformation of its products. Rights to the provider data and the derived production coefficients and results were not established; the latter are intentionally omitted as a precaution. This does not determine whether a particular use or publication is legally prohibited. Users must obtain any appropriate authorization and investigate provider terms independently. Neither the MIT code license nor attribution grants data rights.

Synthetic tests establish the behavior of included code, not the historical metrics or production performance. Historical training and saved-result verification require separately authorized source-format inputs. Retraining has not been rerun for this release. Scripts that write outputs should be run only in a disposable isolated copy.

The release was screened for secret-looking strings, URLs, administrative routes, databases, data archives and production artifacts. Such a review cannot guarantee detection of every possible issue, nor does it replace verification of authorship or third-party rights. This package does not alter the website or its updater.
