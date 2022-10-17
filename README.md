# **U19 Data Sharing Portal (USArhythms, aABC)**

***Centralised Portal*** aims to warehouse meta-data about shared research, including indexing, searching and pointers to code/visualization tools

***Production Deployments***: 
- https://usarhythms.ucsd.edu/ (USArhythms U19 Portal)
- https://highandlow.dk.ucsd.edu/ (aABC U19 Portal)

## Steps for setup:

    1. Create VM running NGINX
    2. Create python virtual environment on webserver (outside of NGINX document root)
    3. Setup gunicorn (see ref below for Ubuntu 22.04)
    4. Point DNS A record to web server and add TLS certificate (see ref2 below)
    5. Create/edit local_settings.py to connect to local database

ref: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04
ref2: https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-22-04

## Features

---

- Permits user login to data sharing portal
- Provides user input form for experimental meta-data
- Provides user search form for locating previously-entered data


## Future goals

---
- Add basic visualizations for common data formats
- Add API for external/automated experimental data additions

## Contribute

---

[Issue Tracker] (https://github.com/drinehart1/USArhythms/issues)

[Source Code] (https://github.com/drinehart1/USArhythms)

## Support

---

If you are having issues, please let me know.
Duane Rinehart - drinehart@ucsd.edu

## License

---
The project is licensed under the [MIT license](https://mit-license.org/).
