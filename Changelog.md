## 1.0
* Add CSP support
* Add dnt-helper for handling DNT
* Add redis support
* Use hashes for pip
* Add station information on Data API endpoint
* Add pass details to payload frame
* Add max freq range to antenna
* Add polar plot on upcoming observations
* Filter and not predict on missing frequency capabilities

## 0.9

* Add a satellite current position endpoint for DB to consume
* Fix long paginator on Observations list
* Add linters for css/js
* Add option for deleting empty observations
* Rearrange data view in observation view with tabs
* Add spectrogram generation on audio tab

## 0.8

* Add basic form validation on Stations and Observations
* Add modal with Satellite information and DB link
* Create permalink to hightlight observation data blocks
* Add DemodData model to handle multiple demodulated payload
* Add option for adding TLEs manually
* Add travis support
* Switch to bower for static
* Add pagination to API
* Add pagination to Observations
* Add initial tests to get 75% coverage

## 0.7

* Display current playback time for observation data
* Observation timeline adapt to mobile
* Collapse station next satellite passes
* Implement a configurable minimum horizon in network
* Provide all settings client needs through API
* Observation data vetting/verification system
* Simplify UI for observation data panels
* Use UTC on observations
* Filter observations based on data verification
* Filter observations by satellite
* Include modulation on API Jobs endpoint
* Add a new payload field on Data model
* Add selector for prefilling satellite on new observations
* Satellite modal on observations

## 0.6

* Add new Antenna types
* Next satellites to pass on each Station
* Keep TLE historical data
* Show TLEs used on Observations

## 0.5

* Hide satellites with no transmitters
* Success rate for Ground Stations
* Sync MODES from DB
* Allow user to delete Scheduled Observations
* Add ability to delete a Ground Station
* Add initialize command to help developers
* Add Discussion button on Observations
* Exclude overlapped timeframe from observations
* Compress static files

## 0.4

* Rename Transponders to Transmitters
* Hide unused API endpoints

## 0.3

* Last Seen feature on Ground Stations
* Enhance Observations UI
* Opbeat
* Add custom 404/500 pages
* robots.txt
* Add site settings for fetching data

## 0.2

* UI improvements

## 0.1

* Initial release
