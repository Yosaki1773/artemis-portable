import sys
import pygit2

ARTEMIS_REPO = sys.argv[1]
ARTEMIS_BRANCH = sys.argv[2]

repo = pygit2.Repository("artemis/.git")

repo.config.set_multivar("remote.origin.url", "", ARTEMIS_REPO)

branch = repo.lookup_branch(ARTEMIS_BRANCH)
ref = repo.lookup_reference(branch.name)
repo.checkout(ref)

for remote in repo.remotes:
    if remote.name != "origin":
        continue

    remote.fetch()

    remote_master_id = repo.lookup_reference(
        f"refs/remotes/origin/{ARTEMIS_BRANCH}"
    ).target
    merge_result, _ = repo.merge_analysis(remote_master_id)

    if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
        print("[INFO] ARTEMiS is up to date.")
    elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
        repo.checkout_tree(repo.get(remote_master_id))

        master_ref = repo.lookup_reference(f"refs/heads/{ARTEMIS_BRANCH}")

        master_ref.set_target(remote_master_id)
        repo.head.set_target(remote_master_id)
    elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
        print(
            "[ERROR] You have local changes that leads to a conflict. good luck lmao."
        )
        exit(1)
