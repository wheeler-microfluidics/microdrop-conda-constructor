"%PYTHON%" -m pip install --find-links http://192.99.4.95/wheels --trusted-host 192.99.4.95 "microdrop=={{ version }}"
if errorlevel 1 exit 1

:: Add more build steps here, if they are necessary.

:: See
:: http://docs.continuum.io/conda/build.html
:: for a list of environment variables that are set during the build process.
REM copy menu-windows.json %MENU_DIR%\

:: copy %RECIPE_DIR%\IPython.ico %MENU_DIR%\
