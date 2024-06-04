# FCS-Visualiser
[![Streamlit](https://img.shields.io/badge/Powered_by-Streamlit-red?logo=streamlit)](https://streamlit.io/])

An interactive web app to quickly visualise ToF data recorded by the FCS setup

## What's what?

* `FCS-Visualiser.py`: main code to run the web app
* `pages`: folder containing subpages of the web app
* `modules`: folder containing dependencies of the main code
* `CONTRIBUTING.md`: how to contribute to this project
* `environment.yml`: portable conda environment description file
* `masses.npy`: library containing the peak identifyers

## How to use?

Simply run the main program!

```
$ streamlit run FCS-Visualiser.py
```

A `defaults.ini` file will be generated the first time this program is being run. You can change the `directory` option to indicate the starting directory when selecting the data.
