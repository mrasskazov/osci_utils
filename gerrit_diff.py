#!/usr/bin/env python
#-*- coding: utf-8 -*-

import logging
import re

from git import Repo

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('gerrit_diff')


def main():

    repo_path = '/home/rmv/devel/mirantis/osci/fuel/fuel-main'
    dst_branch = 'master'
    src_branch = 'stable/5.0'

    repo = Repo.init(repo_path)
    git = repo.git
    dst = repo.heads[dst_branch]
    src = repo.heads[src_branch]
    merge_base = repo.commit(git.merge_base(dst.name, src.name))

    ischid = re.compile(r'^change-id:.*', re.IGNORECASE)

    dst_chids = list()
    for c in repo.iter_commits('{}..{}'.format(merge_base.hexsha, dst.name),
                               no_merges=True):
        message = re.split(r'\n+', c.message)
        for l in message:
            if ischid.match(l) is not None:
                dst_chids.append(re.split(r'\W+', l)[-1])

    src_commits = list()
    for c in repo.iter_commits('{}..{}'.format(merge_base.hexsha, src.name),
                               no_merges=True):
        message = re.split(r'\n+', c.message)
        for l in message:
            if ischid.match(l) is not None:
                chid = re.split(r'\W+', l)[-1]
                if chid not in dst_chids:
                    src_commits.append(c)
                    logger.info('Adding {} - Change-Id {} is absent in {}'.
                                format(c.hexsha, chid, dst.name))
                else:
                    logger.debug('Skiping {} - Change-Id {} already in {}'.
                                 format(c.hexsha, chid, dst.name))
                break
        else:
            src_commits.append(c)
            logger.info('Adding {} - has no Change-ID in commit message'.
                        format(c.hexsha))

    for c in src_commits:
        print('{} {} --- {}'.format(c.hexsha, c.author, c.summary))


if __name__ == '__main__':
    main()
