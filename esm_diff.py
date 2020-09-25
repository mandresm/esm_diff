import os
import subprocess
import argparse
import math

def missf(f1, f2, name1, name2, cathegory):
    name1 = str(name1)
    name2 = str(name2)

    common_files = []

    print('\n'*vsp, cathegory, name1, 'missing in', name2, '\n', '-'*40)
    not_found = []
    for ff in f1:
        if ff not in f2:
            if cathegory=='File' or cathegory=='Folder':
                not_found.append(ff)
            elif cathegory=='FileType':
                u = ff.find('.nc')
                f = ff[0:u]
                e = f[-1]
                while e.isdigit():
                    f = f[:-1]
                    e = f[-1]
                found = False
                for f22 in f2:
                    if f in f22:
                        found = True
                        break
                if not found:
                    if f not in not_found:
                        not_found.append(f)
        else:
            common_files.append(ff)
    cprint(not_found)
    return common_files

def cprint(clist):
    # Read width of the console
    rows, columns = os.popen('stty size', 'r').read().split()
    columns = int(columns)
    # Largest string length in the list
    if len(clist)==0:
        llen = 1
    else:
        llen = len(max(clist, key=len)) + 4
    # Find number of printing columns
    num_columns = int(columns/llen)

    # Sort clist
    clist = sorted(clist)
    # Indexes for correct ordering in columns
    if len(clist) > 0:
        col_len = math.ceil(len(clist)/num_columns)
        col_indx = []
        for col in range(col_len):
            iline = [*range(col, len(clist), col_len)]
            for i in range(len(iline), num_columns):
                iline.append(None)
            col_indx.extend(iline)

        for count, indx in enumerate(col_indx, 1):
            if  indx is not None:
                print(clist[indx].ljust(llen),end='')
            if count % num_columns == 0:
                print()

# Vertical spacing for output
vsp = 3
# CDO binary
cdo = '/global/AWIsoft/cdo/1.9.6/bin/cdo'

# Default directory
esm_diff_dir = os.path.expanduser('~') + '/esm_diff/'
# File for saving differences
ndfile = esm_diff_dir + 'esm_diff.out'
# Current path
cwd = os.getcwd()

# Get arguments
parser = argparse.ArgumentParser(description='Find differences among the specified directories')
parser.add_argument('d1', default=None, nargs='+')
parser.add_argument('d2', default=None)
parser.add_argument('-k', '--keyword', default=False)

args = vars(parser.parse_args())

# Load directories
d1 = args['d1']
d2 = args['d2']

# Load keyword
kw = args['keyword']

# List files and folders
f1 = []
c1 = []
for c, path in enumerate(d1):
    ls = os.listdir(path)
    f1 += ls
    c1 += [c] * len(ls)
f2 = os.listdir(d2)

# Clasify files and folders
files1 = []
files2 = []
folders1 = []
folders2 = []
c11 = []
for f, c in zip(f1, c1):
    if os.path.isfile(d1[c] + '/' + f):
        if kw:
            if kw in f:
                files1.append(f)
        else:
            files1.append(f)
    else:
        folders1.append(f)
for f in f2:
    if os.path.isfile(d2 + '/' + f):
        files2.append(f)
    else:
        folders2.append(f)

missf(folders1, folders2, 1, 2, 'Folder')
missf(folders2, folders1, 2, 1, 'Folder')

ftype = input('\n'*vsp + 'Would you like to display missing files (f) or file types (t)? ')
t = dict(f='File', t='FileType')
common_files1 = missf(files1, files2, 1, 2, t[ftype])
common_files2 = missf(files2, files1, 2, 1, t[ftype])

common_index = []
for cf in common_files1:
    common_index.append(c1[f1.index(cf)])

check_str = 'cdo diff: Processed'
l = len(check_str)

input('\n'*vsp + 'Press Enter to continue...' + '\n'*vsp)
subprocess.call(['module load cdo'], shell=True)
dfiles = []
ifiles = []
niter = len(common_files1)
with open(ndfile,'w') as df:
    df.write('FILE DIFFERENCES\n\n\n')
    df.write('Compared contents of:\n')
    for path in d1:
        df.write('  ' + cwd + path + '\n')
    df.write('with contents of:\n')
    df.write('  ' + cwd + d2 + '\n')
    if kw:
        df.write('Key: ' + kw + '\n')
    df.write('\n'*3)
for c, f in enumerate(common_files1):
    file1 = d1[common_index[c]] + '/' + f
    file2 = d2 + '/' + f
    mf = []
    if not os.path.isfile(file1):
        mf += file1
    if not os.path.isfile(file2):
        mf += file2
    if len(mf)>0:
        raise Exception('Missing files:', mf)
    p = subprocess.Popen([cdo, 'diff', file1, file2], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.communicate()[0].decode('utf-8')
    if len(out)>0:
        print(out)
        with open(ndfile,'a') as df:
            title = '\n\n\n' + '=' * len(f) + '\n' + f + '\n' + '=' * len(f) + '\n\n'
            df.write(title)
            df.write(out)
        dfiles.append(f)
    else:
        ifiles.append(f)
    run = c/niter
    rep = 50
    print('|' + u'\u2588' * round(rep*run) + ' ' * round(rep*(1-run)) + '| ' + str(round(run*1000)/10) + '%   ' + f + ' '*10, end="\r")

print('|' + u'\u2588' * rep + '| ' + '100%   ' + f + ' '*10, end="\r")

print()

if len(dfiles)==0:
    print('\n\nThe following files are identical:')
    cprint(ifiles)
    print('\n\nNo differences found in any file\n\n')
    with open(ndfile,'a') as df:
        df.write('\n\nThe following files are identical:\n\n')
        for f in ifiles:
            df.write(f + '\n')
        df.write('\n\nNo differences found in any file\n\n')
else:
    with open(ndfile,'a') as df:
        df.write('\n\nThe following files are different:\n\n')
        for f in dfiles:
            df.write(f + '\n')
        df.write('\n\nThe following files are identical:\n\n')
        for f in ifiles:
            df.write(f + '\n')
        df.write('Files compared:  ' + str(len(common_files1)) + '\n')
        df.write('Different files: ' + str(len(dfiles)) + '\n')
    print('The following files are different:')
    cprint(dfiles)
    print('\n\nThe following files are identical:')
    cprint(ifiles)
    print('\n\nFiles compared:  ' + str(len(common_files1)))
    print('Different files: ' + str(len(dfiles)))
