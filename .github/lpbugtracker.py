#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vi: set ft=python :
"""
Launchpad Bug Tracker uses launchpadlib to get the bugs.

Based on https://github.com/ubuntu/yaru/blob/master/.github/lpbugtracker.py
"""

import os
import subprocess
import logging
import json

from launchpadlib.launchpad import Launchpad

log = logging.getLogger("lpbugtracker")
log.setLevel(logging.DEBUG)

GH_OWNER = "bluesabre"
GH_REPO = "menulibre"

LP_SOURCE_NAME = "menulibre"
LP_SOURCE_URL_NAME = "menulibre"

HOME = os.path.expanduser("~")
CACHEDIR = os.path.join(HOME, ".launchpadlib", "cache")

LP_OPEN_STATUS_LIST = ["New",
                       "Opinion",
                       "Confirmed",
                       "Triaged",
                       "In Progress",
                       "Fix Committed",
                       "Incomplete"]
LP_CLOSED_STATUS_LIST = ["Invalid",
                         "Won't Fix",
                         "Expired",
                         "Fix Released"]


def main():
    lp_bugs = get_lp_bugs()
    if len(lp_bugs) == 0:
        return

    gh_bugs = get_gh_bugs()

    for id in lp_bugs:
        if id in gh_bugs.keys():
            last_comment_id = get_gh_last_lp_comment(gh_bugs[id]["id"])
            add_comments(gh_bugs[id]["id"], last_comment_id, lp_bugs[id]["messages"])

            gh_labels = parse_gh_labels(gh_bugs[id]["labels"])
            if lp_bugs[id]["closed"] and gh_bugs[id]["status"] != "closed":
                close_issue(gh_bugs[id]["id"], gh_labels["labels"], lp_bugs[id]["status"])
            elif lp_bugs[id]["status"] != gh_labels["status"]:
                update_issue(gh_bugs[id]["id"], gh_labels["labels"], lp_bugs[id]["status"])
        elif not lp_bugs[id]["closed"] and lp_bugs[id]["status"] != "Incomplete":
            bug_id = create_issue(id, lp_bugs[id]["title"], lp_bugs[id]["link"], lp_bugs[id]["status"])
            add_comments(bug_id, -1, lp_bugs[id]["messages"])


def get_lp_bugs():
    """Get a list of bugs from Launchpad"""

    package = lp_get_package(LP_SOURCE_NAME)
    open_bugs = lp_package_get_bugs(package, LP_OPEN_STATUS_LIST, True)
    closed_bugs = lp_package_get_bugs(package, LP_CLOSED_STATUS_LIST, False)

    return {**open_bugs, **closed_bugs}


def get_gh_bugs():
    """Get the list of the LP bug already tracked in GitHub.

    Launchpad bugs tracked on GitHub have a title like

    "LP#<id> <title>"

    this function returns a list of the "LP#<id>" substring for each bug,
    open or closed, found on the repository on GitHub.
    """

    output = subprocess.check_output(
        ["hub", "issue", "--labels", "Launchpad", "--state", "all", "--format", "%I|%S|%L|%t%n"]
    )
    bugs = {}
    for line in output.decode().split("\n"):
        issue = parse_gh_issue(line)
        if issue is not None:
            bugs[issue["lpid"]] = issue
    return bugs


def create_issue(id, title, weblink, status):
    """ Create a new Bug using HUB """
    print("creating:", id, title, weblink, status)
    return gh_create_issue("LP#{} {}".format(id, title),
                           "Reported first on Launchpad at {}".format(weblink),
                           "Launchpad,%s" % status)


def update_issue(id, current_labels, status):
    """ Update a Bug using HUB """
    print("updating:", id, status)
    new_labels = ["Launchpad", status] + current_labels
    gh_set_issue_labels(id, ",".join(new_labels))


def close_issue(id, current_labels, status):
    """ Close the Bug using HUB and leave a comment """
    print("closing:", id, status)
    new_labels = ["Launchpad", status] + current_labels
    gh_add_comment(id, "Issue closed on Launchpad with status: {}".format(status))
    gh_close_issue(id, ",".join(new_labels))


def add_comments(issue_id, last_comment_id, comments):
    for id in comments:
        if id > last_comment_id:
            print("adding comment:", issue_id, id)
            gh_add_comment(issue_id, format_lp_comment(comments[id]))


def quote_str(string):
    content = []
    for line in string.split("\n"):
        content.append("> {}".format(line))
    return "\n".join(content)


def format_lp_comment(message):
    output = "[LP#{}]({}): *{} ({}) wrote on {}:*\n\n{}".format(message["id"],
                                                                message["link"],
                                                                message["author"]["display_name"],
                                                                message["author"]["name"],
                                                                message["date"],
                                                                quote_str(message["content"]))
    if len(message["attachments"]) > 0:
        output += "\n\nAttachments:"
        for attachment in message["attachments"]:
            output += "\n- [{}]({})".format(attachment["title"],
                                            attachment["link"])
    return output


def parse_gh_issue(issue):
    if "LP#" in issue:
        id, status, labels, lp = issue.strip().split("|", 3)
        labels = labels.split(", ")
        lpid, title = lp.split(" ", 1)
        lpid = lpid[3:]
        return {"id": id, "lpid": lpid, "status": status, "title": title, "labels": labels}
    return None


def parse_gh_labels(labels):
    result = {
        "status": "Unknown",
        "labels": []
    }
    for label in labels:
        if label == "Launchpad":
            continue
        elif label in LP_OPEN_STATUS_LIST + LP_CLOSED_STATUS_LIST:
            result["status"] = label
        else:
            result["labels"].append(label)
    return result


def get_gh_last_lp_comment(issue_id):
    comments = gh_list_comments(issue_id)
    last_comment_id = -1
    for comment in comments:
        if comment["body"][0:4] == "[LP#":
            comment_id = comment["body"].split("]")[0]
            comment_id = comment_id[4:]
            comment_id = int(comment_id)
            if comment_id > last_comment_id:
                last_comment_id = comment_id
    return last_comment_id


# Launchpad API
def lp_get_package(source_name):
    lp = Launchpad.login_anonymously(
        "%s LP bug checker" % LP_SOURCE_NAME, "production", CACHEDIR, version="devel"
    )

    ubuntu = lp.distributions["ubuntu"]
    archive = ubuntu.main_archive

    packages = archive.getPublishedSources(source_name=source_name)
    package = ubuntu.getSourcePackage(name=packages[0].source_package_name)

    return package


def lp_package_get_bugs(package, status_list, get_messages = False):
    """Get a list of bugs from Launchpad"""

    bug_tasks = package.searchTasks(status=status_list)
    bugs = {}

    for task in bug_tasks:
        bug = lp_task_get_bug(task, get_messages)
        if bug is not None:
            bugs[bug["id"]] = bug

    return bugs


def lp_task_get_bug(task, get_messages = False):
    try:
        id = str(task.bug.id)
        title = task.title.split(": ", 1)[1]
        status = task.status
        closed = status in LP_CLOSED_STATUS_LIST
        link = "https://bugs.launchpad.net/ubuntu/+source/{}/+bug/{}".format(LP_SOURCE_URL_NAME, id)
        if get_messages:
            messages = lp_bug_get_messages(task.bug)
        else:
            messages = {}
        return {"id": id, "title": title, "link": link, "status": status, "closed": closed, "messages": messages}
    except:
        return None


def lp_bug_get_messages(bug):
    messages = {}
    for message in bug.messages:
        message_id = lp_message_get_id(message)
        messages[message_id] = {
            "id": str(message_id),
            "link": message.web_link,
            "content": message.content,
            "date": lp_message_get_date_time(message),
            "author": lp_message_get_author(message),
            "attachments": lp_message_get_attachments(message)
        }
    return messages


def lp_message_get_author(message):
    return {
        "name": message.owner.name,
        "display_name": message.owner.display_name,
    }


def lp_message_get_id(message):
    return int(message.web_link.split("/")[-1])


def lp_message_get_date_time(message):
    dt = message.date_created
    dt = dt.isoformat().split(".")[0]
    dt = dt.split("T")[0]
    return dt


def lp_message_get_attachments(message):
    attachments = []
    for attach in message.bug_attachments:
        attachments.append({
            "link": attach.data_link,
            "title": attach.title
        })
    return attachments


# GitHub API
def gh_create_issue(summary, description, labels):
    url = subprocess.check_output(
        [
            "hub",
            "issue",
            "create",
            "--message",
            summary,
            "--message",
            description,
            "-l",
            labels
        ]
    )
    url = url.decode("utf-8")
    url = url.strip()
    id = url.split("/")[-1]
    return id


def gh_set_issue_labels(id, labels):
    subprocess.run(
        [
            "hub",
            "issue",
            "update",
            id,
            "-l",
            labels,
        ]
    )


def gh_close_issue(id, labels):
    subprocess.run(
        [
            "hub",
            "issue",
            "update",
            id,
            "--state",
            "closed",
            "-l",
            labels,
        ]
    )


def gh_add_comment(issue_id, comment):
    subprocess.run(
        [
            "hub",
            "api",
            "repos/{}/{}/issues/{}/comments".format(GH_OWNER, GH_REPO, issue_id),
            "--field",
            "body={}".format(comment)
        ]
    )


def gh_list_comments(issue_id):
    output = subprocess.check_output(
        [
            "hub",
            "api",
            "repos/{}/{}/issues/{}/comments".format(GH_OWNER, GH_REPO, issue_id)
        ]
    )
    return json.loads(output)


if __name__ == "__main__":
    main()
