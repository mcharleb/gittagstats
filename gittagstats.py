##############################################################################
# Copyright (c) 2015, Mark Charlebois
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE
# GRANTED BY THIS LICENSE.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT
# HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##############################################################################
'''
Generate reports for a git repo based on a set of tags.
The report will summarize the commit stats for all commits between the current and previous tag.
The data can be presented in a table or as a list of the changes.
'''

import os
import git
from prettytable import PrettyTable

class TagStats:
	def __init__(self):
		self.authors = {}
		self.stats = (0, 0, 1)
		self.commits = []
		self.files = {}

class Group:
	def __init__(self, name, whitelist, blacklist = []):
		self.name = name
		self.whitelist = whitelist
		self.blacklist = blacklist
		self.tags = {}

	def add_tag(self, tag):
		if tag in self.tags.keys():
			print "Warning tag ", tag, "already exists, reinitializing"
		self.tags[tag] = TagStats()

	def add_commit(self, tag, cid, email, insertions, deletions, filename):
		if not tag in self.tags.keys():
			print "Error: call add_tag(tag) once before calling add_commit(tag,...)"

		if email in self.tags[tag].authors.keys():
			self.tags[tag].authors[email] += 1
		else:
			self.tags[tag].authors[email] = 1

		self.tags[tag].stats = tuple(sum(x) for x in zip(self.tags[tag].stats, (insertions, deletions, 1)))
		self.tags[tag].commits.append(cid)
		if filename in self.tags[tag].files.keys():
			self.tags[tag].files[filename] = tuple(sum(x) for x in zip(self.tags[tag].files[filename], (insertions, deletions, 1)))
		else:
			self.tags[tag].files[filename] = (insertions, deletions, 1)

	def get_commits(self, tag):
		return [ self.tags[tag].commits, self.tags[tag].files, self.tags[tag].authors ]

class Report:
	def __init__(self, repo, tags, patterns, files, groups):
		self.repo = repo
		self.tags = tags
		self.patterns = patterns
		self.files = files
		self.groups = groups

	def generate(self):
		for i in range(0, len(self.tags)-1):
			print "Computing", self.tags[i+1], "..."
			self._get_commits(self.tags[i], self.tags[i+1])

	def show_table(self):
		for g in self.groups:
			t = PrettyTable(['Version', 'Files Changed', 'Insertions', 'Deletions', '# Commits', '# Contrib'])
			for x in self.tags[1:]:
				if x in g.tags.keys():
					a = (x, len(g.tags[x].files.keys()))
					b = (len(g.tags[x].authors.keys()),)
					tup = a + g.tags[x].stats + b
					t.add_row(tup)
			print g.name+":"
			print t

	def show_table_csv(self):
		for g in self.groups:
			for x in self.tags[1:]:
				if x in g.tags.keys():
					num_authors = (len(g.tags[x].authors.keys()),)
					tup = g.tags[x].stats + num_authors
					num_files = len(g.tags[x].files.keys())
					print "{0}, {1}, {3}, {4}, {5}".format(g.name, x, num_files, *tup)

	def show_commits(self):
		for g in self.groups:
			for t in g.tags.keys():
				[ commits, files, authors ] = g.get_commits(t)
				print g.name, t+":"
				lines = self.repo.git.show("--oneline", *commits).split("\n")
				print "\tCommits" 
				for c in commits:
					print "\t\t", c
				print "\tFiles:"
				for a in files.keys():
					print "\t\t", a, "insertions: {0} deletions: {1} commits {2}".format(*files[a])
				print "\tAuthors:"
				for a in authors.keys():
					print "\t\t", a, authors[a]
				
		
	def _get_commits(self, tag1, tag2):
		search_set = [ '--grep="{0}"'.format(x) for x in self.patterns ]
		search_set += self.files
		commitlist = self.repo.git.log("--no-merges", "--numstat", "{0}..{1}".format(tag1, tag2), '--format=#%h:%ae', "--", *search_set).split("#")[1:]

		# Initialize the tag stats for each group
		for g in self.groups:
			g.add_tag(tag2)

		for c in commitlist:
			commit = c.split("\n")[:-1]
			if not commit[0]:
				continue
			[cid, email] = commit[0].split(":")
			for g in self.groups:
				cond1 = not g.whitelist or filter(lambda a: a in email, g.whitelist)
				cond2 = not g.blacklist or not filter(lambda a: a in email, g.blacklist)
				if cond1 and cond2:
					for diff in commit[2:]:
						( insertions, deletions, filename ) = diff.split("\t")
						g.add_commit(tag2, cid, email, int(insertions), int(deletions), filename)


