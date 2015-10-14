from datetime import datetime
import os
import shutil
import sys
import traceback

from DDR import changelog
from DDR import config
from DDR import dvcs
from DDR import fileio
from DDR import identifier
from DDR import imaging
from DDR import util


class AddFileLogger():
    logpath = None
    
    def entry(self, ok, msg ):
        """Returns log of add_files activity; adds an entry if status,msg given.
        
        @param ok: Boolean. ok or not ok.
        @param msg: Text message.
        @returns log: A text file.
        """
        entry = '[{}] {} - {}\n'.format(datetime.now().isoformat('T'), ok, msg)
        with open(self.logpath, 'a') as f:
            f.write(entry)
    
    def ok(self, msg): self.entry('ok', msg)
    def not_ok(self, msg): self.entry('not ok', msg)
    
    def log(self):
        log = ''
        if os.path.exists(self.logpath):
            with open(self.logpath, 'r') as f:
                log = f.read()
        return log

def _log_path(entity):
    """Generates path to collection addfiles.log.
    
    Previously each entity had its own addfile.log.
    Going forward each collection will have a single log file.
        /STORE/log/REPO-ORG-CID-addfile.log
    
    @returns: absolute path to logfile
    """
    logpath = os.path.join(
        config.LOG_DIR, 'addfile', entity.parent_id, '%s.log' % entity.id)
    if not os.path.exists(os.path.dirname(logpath)):
        os.makedirs(os.path.dirname(logpath))
    return logpath

def addfile_logger(entity):
    log = AddFileLogger()
    log.logpath = _log_path(entity)
    return log

def _predict_staged(entity, already, planned):
    """Predict which files will be staged, accounting for modifications
    
    When running a batch import there will already be staged files when this function is called.
    Some files to be staged will be modifications (e.g. entity.json).
    Predicts the list of files that will be staged if this round of add_file succeeds.
    how many files SHOULD be staged after we run this?
    
    @param already: list Files already staged.
    @param planned: list Files to be added/modified in this operation.
    @returns: list
    """
    additions = [path for path in planned if path not in already]
    total = already + additions
    return total

def add_file(entity, src_path, role, data, git_name, git_mail, agent=''):
    """Add file to entity
    
    This method breaks out of OOP and manipulates entity.json directly.
    Thus it needs to lock to prevent other edits while it does its thing.
    Writes a log to ${entity}/addfile.log, formatted in pseudo-TAP.
    This log is returned along with a File object.
    
    IMPORTANT: Files are only staged! Be sure to commit!
    
    @param src_path: Absolute path to an uploadable file.
    @param role: Keyword of a file role.
    @param data: 
    @param git_name: Username of git committer.
    @param git_mail: Email of git committer.
    @param agent: (optional) Name of software making the change.
    @return File,repo,log
    """
    f = None
    repo = None
    log = addfile_logger(entity)
    
    def crash(msg):
        """Write to addfile log and raise an exception."""
        log.not_ok(msg)
        raise Exception(msg)
    
    log.ok('------------------------------------------------------------------------')
    log.ok('DDR.models.Entity.add_file: START')
    log.ok('entity: %s' % entity.id)
    log.ok('data: %s' % data)
    
    tmp_dir = os.path.join(
        config.MEDIA_BASE, 'tmp', 'file-add', entity.parent_id, entity.id)
    dest_dir = entity.files_path
    
    log.ok('Checking files/dirs')
    def check_dir(label, path, mkdir=False, perm=os.W_OK):
        log.ok('%s: %s' % (label, path))
        if mkdir and not os.path.exists(path):
            os.makedirs(path)
        if not os.path.exists(path): crash('%s does not exist' % label)
        if not os.access(path, perm): crash('%s not has permission %s' % (label, permission))
    check_dir('| src_path', src_path, mkdir=False, perm=os.R_OK)
    check_dir('| tmp_dir', tmp_dir, mkdir=True, perm=os.W_OK)
    check_dir('| dest_dir', dest_dir, mkdir=True, perm=os.W_OK)
    
    log.ok('Checksumming')
    md5    = util.file_hash(src_path, 'md5');    log.ok('| md5: %s' % md5)
    sha1   = util.file_hash(src_path, 'sha1');   log.ok('| sha1: %s' % sha1)
    sha256 = util.file_hash(src_path, 'sha256'); log.ok('| sha256: %s' % sha256)
    if not sha1 and md5 and sha256:
        crash('Could not calculate checksums')
    
    log.ok('Identifier')
    idparts = {
        'role': role,
        'sha1': sha1[:10],
    }
    log.ok('| idparts %s' % idparts)
    fidentifier = entity.identifier.child('file', idparts, entity.identifier.basepath)
    log.ok('| identifier %s' % fidentifier)
    
    log.ok('Destination path')
    src_ext = os.path.splitext(src_path)[1]
    dest_basename = '{}{}'.format(fidentifier.id, src_ext)
    log.ok('| dest_basename %s' % dest_basename)
    dest_path = os.path.join(dest_dir, dest_basename)
    log.ok('| dest_path %s' % dest_path)
    
    log.ok('File object')
    file_class = fidentifier.object_class()
    file_ = file_class(path_abs=dest_path, identifier=fidentifier)
    file_.basename_orig = os.path.basename(src_path)
    # add extension to path_abs
    basename_ext = os.path.splitext(file_.basename_orig)[1]
    path_abs_ext = os.path.splitext(file_.path_abs)[1]
    if basename_ext and not path_abs_ext:
        file_.path_abs = file_.path_abs + basename_ext
        log.ok('basename_ext %s' % basename_ext)
    log.ok('file_.path_abs %s' % file_.path_abs)
    file_.size = os.path.getsize(src_path)
    file_.role = role
    file_.sha1 = sha1
    file_.md5 = md5
    file_.sha256 = sha256
    log.ok('| file_ %s' % file_)
    log.ok('| file_.basename_orig: %s' % file_.basename_orig)
    log.ok('| file_.path_abs: %s' % file_.path_abs)
    log.ok('| file_.size: %s' % file_.size)
    # form data
    for field in data:
        setattr(file_, field, data[field])
    
    log.ok('Copying to work dir')
    log.ok('tmp_dir exists: %s (%s)' % (os.path.exists(tmp_dir), tmp_dir))
    tmp_path = os.path.join(tmp_dir, file_.basename_orig)
    log.ok('| cp %s %s' % (src_path, tmp_path))
    shutil.copy(src_path, tmp_path)
    os.chmod(tmp_path, 0644)
    if os.path.exists(tmp_path):
        log.ok('| done')
    else:
        crash('Copy failed!')
    
    tmp_path_renamed = os.path.join(os.path.dirname(tmp_path), dest_basename)
    log.ok('Renaming %s -> %s' % (os.path.basename(tmp_path), dest_basename))
    os.rename(tmp_path, tmp_path_renamed)
    if not os.path.exists(tmp_path_renamed) and not os.path.exists(tmp_path):
        crash('File rename failed: %s -> %s' % (tmp_path, tmp_path_renamed))
    
    log.ok('Extracting XMP data')
    file_.xmp = imaging.extract_xmp(src_path)
    
    log.ok('Making access file')
    access_filename = file_class.access_filename(tmp_path_renamed)
    access_dest_path = os.path.join(tmp_dir, os.path.basename(access_filename))
    log.ok('src_path %s' % src_path)
    log.ok('access_filename %s' % access_filename)
    log.ok('access_dest_path %s' % access_dest_path)
    log.ok('tmp_dir exists: %s (%s)' % (os.path.exists(tmp_dir), tmp_dir))
    tmp_access_path = None
    try:
        tmp_access_path = imaging.thumbnail(
            src_path,
            access_dest_path,
            geometry=config.ACCESS_FILE_GEOMETRY
        )
    except:
        # write traceback to log and continue on
        log.not_ok(traceback.format_exc().strip())
    if tmp_access_path and os.path.exists(tmp_access_path):
        log.ok('| attaching access file')
        #dest_access_path = os.path.join('files', os.path.basename(tmp_access_path))
        #log.ok('dest_access_path: %s' % dest_access_path)
        file_.set_access(tmp_access_path, entity)
        log.ok('| file_.access_rel: %s' % file_.access_rel)
        log.ok('| file_.access_abs: %s' % file_.access_abs)
    else:
        log.not_ok('no access file')
    
    log.ok('Attaching file to entity')
    entity.files.append(file_)
    if file_ in entity.files:
        log.ok('| done')
    else:
        crash('Could not add file to entity.files!')
    
    log.ok('Writing file metadata')
    tmp_file_json = os.path.join(tmp_dir, os.path.basename(file_.json_path))
    log.ok(tmp_file_json)
    fileio.write_text(file_.dump_json(), tmp_file_json)
    if os.path.exists(tmp_file_json):
        log.ok('| done')
    else:
        crash('Could not write file metadata %s' % tmp_file_json)
    
    log.ok('Writing entity metadata')
    tmp_entity_json = os.path.join(tmp_dir, os.path.basename(entity.json_path))
    log.ok(tmp_entity_json)
    fileio.write_text(entity.dump_json(), tmp_entity_json)
    if os.path.exists(tmp_entity_json):
        log.ok('| done')
    else:
        crash('Could not write entity metadata %s' % tmp_entity_json)
    
    # WE ARE NOW MAKING CHANGES TO THE REPO ------------------------
    
    log.ok('Moving files to dest_dir')
    new_files = [
        [tmp_path_renamed, file_.path_abs],
        [tmp_file_json, file_.json_path],
    ]
    if tmp_access_path and os.path.exists(tmp_access_path):
        new_files.append([tmp_access_path, file_.access_abs])
    mvfiles_failures = []
    for tmp,dest in new_files:
        log.ok('| mv %s %s' % (tmp,dest))
        os.rename(tmp,dest)
        if not os.path.exists(dest):
            log.not_ok('FAIL')
            mvfiles_failures.append(tmp)
            break
    # one of new_files failed to copy, so move all back to tmp
    if mvfiles_failures:
        log.not_ok('%s failures: %s' % (len(mvfiles_failures), mvfiles_failures))
        log.not_ok('Moving files back to tmp_dir')
        try:
            for tmp,dest in new_files:
                log.ok('| mv %s %s' % (dest,tmp))
                os.rename(dest,tmp)
                if not os.path.exists(tmp) and not os.path.exists(dest):
                    log.not_ok('FAIL')
        except:
            msg = "Unexpected error:", sys.exc_info()[0]
            log.not_ok(msg)
            raise
        finally:
            crash('Failed to place one or more files to destination repo')
    else:
        log.ok('| all files moved')
    # entity metadata will only be copied if everything else was moved
    log.ok('Moving entity.json to dest_dir')
    log.ok('| mv %s %s' % (tmp_entity_json, entity.json_path))
    os.rename(tmp_entity_json, entity.json_path)
    if not os.path.exists(entity.json_path):
        crash('Failed to place entity.json in destination repo')
    
    log.ok('Staging files')
    repo = dvcs.repository(file_.collection_path)
    log.ok('| repo %s' % repo)
    log.ok('file_.json_path_rel %s' % file_.json_path_rel)
    git_files = [
        entity.json_path_rel,
        file_.json_path_rel
    ]
    annex_files = [
        file_.path_abs.replace('%s/' % file_.collection_path, '')
    ]
    if file_.access_abs and os.path.exists(file_.access_abs):
        annex_files.append(file_.access_abs.replace('%s/' % file_.collection_path, ''))
    # These vars will be used to determine if stage operation is successful.
    # If called in batch operation there may already be staged files.
    # stage_planned   Files added/modified by this function call
    # stage_already   Files that were already staged
    # stage_predicted List of staged files that should result from this operation.
    # stage_new       Files that are being added.
    stage_planned = git_files + annex_files
    stage_already = dvcs.list_staged(repo)
    stage_predicted = _predict_staged(entity, stage_already, stage_planned)
    stage_new = [x for x in stage_planned if x not in stage_already]
    log.ok('| %s files to stage:' % len(stage_planned))
    for sp in stage_planned:
        log.ok('|   %s' % sp)
    stage_ok = False
    staged = []
    try:
        dvcs.stage(repo, git_files, annex_files)
        staged = dvcs.list_staged(repo)
    except:
        # FAILED! print traceback to addfile log
        log.not_ok(traceback.format_exc().strip())
    finally:
        log.ok('| %s files staged:' % len(staged))
        for sp in staged:
            log.ok('|   %s' % sp)
        if len(staged) == len(stage_predicted):
            log.ok('| %s files staged (%s new, %s modified)' % (
                len(staged), len(stage_new), len(stage_already))
            )
            stage_ok = True
        else:
            log.not_ok('%s new files staged (should be %s)' % (
                len(staged), len(stage_predicted))
            )
        if not stage_ok:
            log.not_ok('File staging aborted. Cleaning up')
            # try to pick up the pieces
            # mv files back to tmp_dir
            # TODO Properly clean up git-annex-added files.
            #      This clause moves the *symlinks* to annex files but leaves
            #      the actual binaries in the .git/annex objects dir.
            for tmp,dest in new_files:
                log.not_ok('| mv %s %s' % (dest,tmp))
                os.rename(dest,tmp)
            log.not_ok('finished cleanup. good luck...')
            raise crash('Add file aborted, see log file for details.')
    
    # IMPORTANT: Files are only staged! Be sure to commit!
    # IMPORTANT: changelog is not staged!
    return file_,repo,log

def add_access( entity, ddrfile, git_name, git_mail, agent='' ):
    """Generate new access file for entity
    
    This method breaks out of OOP and manipulates entity.json directly.
    Thus it needs to lock to prevent other edits while it does its thing.
    Writes a log to ${entity}/addfile.log, formatted in pseudo-TAP.
    This log is returned along with a File object.
    
    TODO Refactor this function! It is waaay too long!
    
    @param ddrfile: File
    @param git_name: Username of git committer.
    @param git_mail: Email of git committer.
    @param agent: (optional) Name of software making the change.
    @return file_ File object
    """
    f = None
    repo = None
    log = addfile_logger(entity)
    
    def crash(msg):
        """Write to addfile log and raise an exception."""
        log.not_ok(msg)
        raise Exception(msg)
    
    src_path = ddrfile.path_abs
    
    log.ok('------------------------------------------------------------------------')
    log.ok('DDR.models.Entity.add_access: START')
    log.ok('entity: %s' % entity.id)
    log.ok('ddrfile: %s' % ddrfile)
    
    tmp_dir = os.path.join(
        config.MEDIA_BASE, 'tmp', 'file-add', entity.parent_id, entity.id)
    dest_dir = entity.files_path
    
    log.ok('Checking files/dirs')
    def check_dir(label, path, mkdir=False, perm=os.W_OK):
        log.ok('%s: %s' % (label, path))
        if mkdir and not os.path.exists(path):
            os.makedirs(path)
        if not os.path.exists(path): crash('%s does not exist' % label)
        if not os.access(path, perm): crash('%s not has permission %s' % (label, permission))
    check_dir('| src_path', src_path, mkdir=False, perm=os.R_OK)
    check_dir('| tmp_dir', tmp_dir, mkdir=True, perm=os.W_OK)
    check_dir('| dest_dir', dest_dir, mkdir=True, perm=os.W_OK)
    
    #log.ok('Checksumming')
    
    log.ok('Identifier')
    log.ok('| file_id %s' % ddrfile.id)
    log.ok('| basepath %s' % entity.identifier.basepath)
    fidentifier = identifier.Identifier(ddrfile.id, entity.identifier.basepath)
    log.ok('| identifier %s' % fidentifier)
    
    #log.ok('Destination path')
    
    log.ok('File object')
    file_class = fidentifier.object_class()
    file_ = file_class(path_abs=src_path, identifier=fidentifier)
    log.ok('| file_ %s' % file_)
    
    #log.ok('Copying to work dir')
    #log.ok('Extracting XMP data')
    
    log.ok('Making access file')
    access_filename = os.path.basename(file_class.access_filename(src_path))
    access_tmp = os.path.join(tmp_dir, access_filename)
    log.ok('| src_path %s' % src_path)
    log.ok('| access_filename %s' % access_filename)
    log.ok('| file_.access_rel: %s' % file_.access_rel)
    log.ok('| file_.access_abs: %s' % file_.access_abs)
    log.ok('| access_tmp %s' % access_tmp)
    log.ok('| tmp_dir exists: %s (%s)' % (os.path.exists(tmp_dir), tmp_dir))
    tmp_access_path = None
    try:
        log.ok('| creating thumbnail: %s' % tmp_access_path)
        tmp_access_path = imaging.thumbnail(
            src_path,
            access_tmp,
            geometry=config.ACCESS_FILE_GEOMETRY
        )
        log.ok('| done')
    except:
        # write traceback to log and continue on
        log.not_ok(traceback.format_exc().strip())
    if tmp_access_path and os.path.exists(tmp_access_path):
        log.ok('| access file exists')
    else:
        crash('Failed to make an access file from %s' % src_path)
    
    #log.ok('Attaching file to entity')
    
    log.ok('Writing file metadata')
    tmp_file_json = os.path.join(tmp_dir, os.path.basename(file_.json_path))
    log.ok('| %s' % tmp_file_json)
    fileio.write_text(file_.dump_json(), tmp_file_json)
    if os.path.exists(tmp_file_json):
        log.ok('| done')
    else:
        crash('Could not write file metadata %s' % tmp_file_json)
    
    #log.ok('Writing entity metadata')
    
    # WE ARE NOW MAKING CHANGES TO THE REPO ------------------------
    
    log.ok('Moving files to dest_dir')
    new_files = []
    if tmp_access_path and os.path.exists(tmp_access_path):
        new_files.append([tmp_access_path, file_.access_abs])
    mvfiles_failures = []
    for tmp,dest in new_files:
        log.ok('| mv %s %s' % (tmp,dest))
        os.rename(tmp,dest)
        if not os.path.exists(dest):
            log.not_ok('FAIL')
            mvfiles_failures.append(tmp)
            break
    # one of new_files failed to copy, so move all back to tmp
    if mvfiles_failures:
        log.not_ok('%s failures: %s' % (len(mvfiles_failures), mvfiles_failures))
        log.not_ok('Moving files back to tmp_dir')
        try:
            for tmp,dest in new_files:
                log.ok('| mv %s %s' % (dest,tmp))
                os.rename(dest,tmp)
                if not os.path.exists(tmp) and not os.path.exists(dest):
                    log.not_ok('FAIL')
        except:
            msg = "Unexpected error:", sys.exc_info()[0]
            log.not_ok(msg)
            raise
        finally:
            crash('Failed to place one or more files to destination repo')
    else:
        log.ok('| all files moved')
    # file metadata will only be copied if everything else was moved
    log.ok('Moving file .json to dest_dir')
    log.ok('| mv %s %s' % (tmp_file_json, file_.json_path))
    os.rename(tmp_file_json, file_.json_path)
    if not os.path.exists(file_.json_path):
        crash('Failed to place file metadata in destination repo')
    
    log.ok('Staging files')
    repo = dvcs.repository(file_.collection_path)
    log.ok('| repo %s' % repo)
    git_files = [
        file_.json_path_rel
    ]
    annex_files = [
        file_.access_rel
    ]
    # These vars will be used to determine if stage operation is successful.
    # If called in batch operation there may already be staged files.
    # stage_planned   Files added/modified by this function call
    # stage_already   Files that were already staged
    # stage_predicted List of staged files that should result from this operation.
    # stage_new       Files that are being added.
    stage_planned = git_files + annex_files
    stage_already = dvcs.list_staged(repo)
    stage_predicted = _predict_staged(entity, stage_already, stage_planned)
    stage_new = [x for x in stage_planned if x not in stage_already]
    log.ok('| %s to stage:' % len(stage_planned))
    log.ok('| %s git files:' % len(git_files))
    for sp in git_files:
        log.ok('|   %s' % sp)
    log.ok('| %s annex files:' % len(annex_files))
    for sp in annex_files:
        log.ok('|   %s' % sp)
    stage_ok = False
    staged = []
    assert False
    try:
        log.ok('dvcs.stage(%s, %s, %s)' % (repo, git_files, annex_files))
        dvcs.stage(repo, git_files, annex_files)
        staged = dvcs.list_staged(repo)
    except:
        # FAILED! print traceback to addfile log
        log.not_ok(traceback.format_exc().strip())
    finally:
        log.ok('| %s files staged:' % len(staged))
        for sp in staged:
            log.ok('|   %s' % sp)
        if len(staged) == len(stage_predicted):
            log.ok('| %s files staged (%s new, %s modified)' % (
                len(staged), len(stage_new), len(stage_already))
            )
            stage_ok = True
        else:
            log.not_ok('%s new files staged (should be %s)' % (
                len(staged), len(stage_predicted))
            )
        if not stage_ok:
            log.not_ok('File staging aborted. Cleaning up')
            # try to pick up the pieces
            # mv files back to tmp_dir
            # TODO Properly clean up git-annex-added files.
            #      This clause moves the *symlinks* to annex files but leaves
            #      the actual binaries in the .git/annex objects dir.
            for tmp,dest in new_files:
                log.not_ok('| mv %s %s' % (dest,tmp))
                os.rename(dest,tmp)
            log.not_ok('finished cleanup. good luck...')
            raise crash('Add file aborted, see log file for details.')
    
    # IMPORTANT: Files are only staged! Be sure to commit!
    # IMPORTANT: changelog is not staged!
    return file_,repo,log

def add_file_commit(entity, file_, repo, log, git_name, git_mail, agent):
    log.ok('add_file_commit(%s, %s, %s, %s, %s, %s)' % (file_, repo, log, git_name, git_mail, agent))
    staged = dvcs.list_staged(repo)
    modified = dvcs.list_modified(repo)
    if staged and not modified:
        log.ok('All files staged.')
        log.ok('Updating changelog')
        path = file_.path_abs.replace('{}/'.format(entity.path), '')
        changelog_messages = ['Added entity file {}'.format(path)]
        if agent:
            changelog_messages.append('@agent: %s' % agent)
        changelog.write_changelog_entry(
            entity.changelog_path, changelog_messages, git_name, git_mail)
        log.ok('git add %s' % entity.changelog_path_rel)
        git_files = [entity.changelog_path_rel]
        dvcs.stage(repo, git_files)
        
        log.ok('Committing')
        commit = dvcs.commit(repo, 'Added entity file(s)', agent)
        log.ok('commit: {}'.format(commit.hexsha))
        committed = dvcs.list_committed(repo, commit)
        committed.sort()
        log.ok('files committed:')
        for f in committed:
            log.ok('| %s' % f)
        
    else:
        log.not_ok('%s files staged, %s files modified' % (len(staged),len(modified)))
        log.not_ok('staged %s' % staged)
        log.not_ok('modified %s' % modified)
        log.not_ok('Can not commit!')
        raise Exception()
    return file_,repo,log
