@echo off
REM --------------------------------------------------
REM Remove 'main' branch and push everything to 'master'
REM --------------------------------------------------

REM 1. Fetch latest from remote
git fetch origin

REM 2. Ensure you’re on master
git checkout master

REM 3. Delete local main branch if it exists
git branch -D main 2>NUL

REM 4. Delete remote main branch
git push origin --delete main 2>NUL

REM 5. Stage all changes
git add .

REM 6. Commit with message
git commit -m "fixed, updates"

REM 7. Push to origin/master
git push -u origin master

PAUSE
