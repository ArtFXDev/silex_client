
# Silex Deadline 

Custom submitters for Artfx's Silex Pipeline.

*This page is work in progress*

## Job

The Job classes are organised in a hierarchy of job types.  
Eg. `VrayJob`, `ÀrnoldJob`

A Job instance implements a job with its job_info and plugin_info.

## JobTree

Not implemented yet.

## DeadlineRunner

The DeadlineRunner holds the connection, wraps the deadline API and submits jobs.


# Testing

rez env silex_client -- python -m "silex_client.utils.deadline.tests.test_arnold"


