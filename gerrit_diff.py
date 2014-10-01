#!/usr/bin/env python
#-*- coding: utf-8 -*-

import logging
import re

from git import Repo
from gerritlib.gerrit import Gerrit
from pprint import pprint

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('gerrit_diff')


def get_attr(commit, regexp):
    message = re.split(r'\n+', commit.message)
    for l in message:
        if regexp.match(l) is not None:
            return re.split(r':\s*', l)[-1]
    return None


def get_change_id(commit):
    ischid = re.compile(r'^change-id:.*', re.IGNORECASE)
    return get_attr(commit, ischid)


def get_attrs(commit, regexp):
    message = re.split(r'\n+', commit.message)
    attrs = list()
    for l in message:
        if regexp.match(l) is not None:
            attrs.append([_.strip() for _ in re.split(r':\s*', l)])
    return attrs


def get_change_id_refs(commit):
    ischidref = re.compile(r'.*change-id.*:.*', re.IGNORECASE)
    return get_attrs(commit, ischidref)


def main():

    repo_path = '/home/rmv/devel/mirantis/osci/fuel/fuel-main'
    dst_branch = 'master'
    src_branch = 'stable/5.1'

    gerrit_hostname = 'review.openstack.org'
    gerrit_username = 'rmv'
    gerrit_port = 29418
    gerrit_keyfile = None

    repo = Repo.init(repo_path)
    git = repo.git
    dst = repo.heads[dst_branch]
    src = repo.heads[src_branch]
    merge_base = repo.commit(git.merge_base(dst.name, src.name))

    dst_chids = list()
    for c in repo.iter_commits('{}..{}'.format(merge_base.hexsha, dst.name),
                               no_merges=True):
        dst_chids.append(get_change_id(c))

    gerrit = Gerrit(gerrit_hostname, gerrit_username,
                    gerrit_port, gerrit_keyfile)

    proposed = gerrit.bulk_query('project:stackforge/fuel-main '
                                 'branch:{} '
                                 'status:open'.
                                 format(dst_branch))
    proposed_chids = list()
    for p in proposed:
        if p.get('id') is not None:
            proposed_chids.append(p['id'])

    src_commits = list()
    for c in repo.iter_commits('{}..{}'.format(merge_base.hexsha, src.name),
                               no_merges=True):
        chid = get_change_id(c)
        if chid is not None:
            if chid not in dst_chids:
                if chid not in proposed_chids:
                    src_commits.append(c)
                    logger.info('Adding {} - Change-Id {} is absent in {} '
                                'and in proposal'.
                                format(c.hexsha, chid, dst.name))
                else:
                    logger.info('Skipping {} - Change-Id {} is absent in {} '
                                 'but exists in proposal'.
                                 format(c.hexsha, chid, dst.name))
            else:
                logger.debug('Skiping {} - Change-Id {} already in {}'.
                             format(c.hexsha, chid, dst.name))
        else:
            src_commits.append(c)
            logger.info('Adding {} - has no Change-ID in commit message'.
                        format(c.hexsha))

    for c in src_commits:
        print('{} {} --- {}'.format(c.hexsha, c.author, c.summary))


if __name__ == '__main__':
    main()
