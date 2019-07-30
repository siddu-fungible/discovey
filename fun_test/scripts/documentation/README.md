The scripts directory has the following layout

1. examples
2. networking
3. storage
4. bugs_and_analyses
5. scratch
6. test_case_spec
7. tasks_spec
8. TBD ....

## bugs_and_analyses

This is the location of
1. scripts used to reproduce a bug
2. scripts used to analyze functionality (repeated trials used to improve performance numbers)

### Guidelines
1. It is required to name the script after the bug say: em_753.py
2. If the software bug ID is not known ahead of time, please file an 'IN' task against yourself, so that the file-name would be something like: in_741.py.
3. After checking in the script, go to http://integration.fungible.local/regression/admin and ensure your script is categorized to Storage/networking etc (not unallocated/unassigned).
4. Ensure your script can run in the Integration regression environment, and the bug can be reproduced.
5. While filing the bug mention the boot-args, Jenkins parameters, the script and a link to script's log files.
6. While filing the bug, also mention the procedure to submit the script: http://confluence.fungible.local/display/SW/Submitting+bug+reproduction+scripts

## test_case_spec
This is location of the various test-suites.
Suites files should end with .json

## tasks_spec


