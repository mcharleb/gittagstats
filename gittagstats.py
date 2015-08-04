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
		self.stats = (0, 0)
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

		self.tags[tag].stats = tuple(sum(x) for x in zip(self.tags[tag].stats, (insertions, deletions)))
		self.tags[tag].commits.append(cid)
		self.tags[tag].files[filename] = 1

	def get_commits(self):
		commits = []
		for t in self.tags.keys():
			commits.append((t, self.tags[t].commits, self.tags[t].authors))
		return commits

class Report:
	def __init__(self, repo, tags, files, groups):
		self.repo = repo
		self.tags = tags
		self.files = files
		self.groups = groups

	def generate(self):
		for i in range(0, len(self.tags)-1):
			self._get_commits(self.tags[i], self.tags[i+1])

	def show_table(self):
		for g in self.groups:
			t = PrettyTable(['Version', 'Files Changed', 'Insertions', 'Deletions', '# Commits', '# Contrib'])
			for x in self.tags[1:]:
				if x in g.tags.keys():
					a = (x, len(g.tags[x].files.keys()))
					b = (len(g.tags[x].commits), len(g.tags[x].authors.keys()))
					tup = a + g.tags[x].stats + b
					t.add_row(tup)
			print g.name+":"
			print t

	def show_commits(self):
		for g in self.groups:
			allcommits = g.get_commits()
			for (tag, commits, authors) in allcommits:
				print g.name, tag+":"
				lines = self.repo.git.show("--shortstat", "--oneline", '--format=%H:%ae:%an ', *commits).split("\n")
				print "\t", lines[0]
				for line in lines[2:]:
					print "\t", line
				print authors
				
		
	def _get_commits(self, tag1, tag2):
		chunks = self.repo.git.log("--no-merges", "--numstat", "{0}..{1}".format(tag1, tag2), '--format=#%H:%ae:%an ', *self.files).split("#")

		# Initialize the tag stats for each group
		for g in self.groups:
			g.add_tag(tag2)

		# skip leading '#'
		for c in chunks[1:]:
			commit = c.split("\n")[:-1]
			if not commit[0]:
				continue
			[cid, email, name] = commit[0].split(":")
			for g in self.groups:
				add_commit = False
				for m in g.whitelist:
					if m in email:
						add_commit = True
						break
				if not g.whitelist:
					add_commit = True

				for m in g.blacklist:
					if m in email:
						add_commit = False
						break
				if add_commit:
					# skip blank line
					for diff in commit[2:]:
						( i, d, filename ) = diff.split("\t")
						insertions = int(i)
						deletions = int(d)
						g.add_commit(tag2, cid, email, insertions, deletions, filename)
						
		
