Mohamed Ala Eddine Bahri
INSIGHT Lab, ISITCom, University of Sousse
Hammam Sousse 4011, Tunisia
bahri.mohamedalaeddine@isitc.u-sousse.tn

To the Editor-in-Chief
*Engineering Applications of Artificial Intelligence*

**Submission of an Original Research article: "A Leakage-Audited Benchmark of
Eleven Intrusion Detectors on GeNIS 2025: Calibration, Cost, and Protocol
Robustness"**

Dear Editor,

We submit the manuscript above for consideration as an Original Research
article.

**The contribution in AI and the application in engineering.** The
contribution in artificial intelligence is a feature-audit protocol of four
complementary tests, each with a stated blind spot, that decides which columns
of a network-flow corpus a learned detector may use, together with the finding
that attribution methods cannot stand in for it: on the corpus studied here,
every one of the eight behavioural shortcuts the protocol removes is scored at
or below 10⁻⁴ by permutation importance, because they are mutually redundant
and six of them are numerically identical columns. The application in
engineering is network intrusion detection on enterprise traffic, evaluated
here on GeNIS 2025, a corpus captured on an industrial CyberRange, with a
second corpus used to test which of the findings carry.

**Fit with the journal.** The scope of *Engineering Applications of Artificial
Intelligence* names "industrial experiences in the application of the above
techniques, e.g. case studies or benchmarking exercises". This paper is such an
exercise made rigorous: eleven supervised detectors and one unsupervised
detector, five seeds, two evaluation protocols, paired significance testing,
and the calibration and single-host inference cost of every model, on a corpus
whose first published numbers are about to become its reference numbers. We
believe the methodological result — that the standard remedies for shortcut
learning, attribution ranking and chronological splitting, were each
insufficient here, and measurably so — is of direct use to anyone deploying a
learned detector on operational traffic.

**Relation to our earlier work.** Three of the neural architectures evaluated
here (the recurrent, convolutional and dense detectors) were first published by
two of the authors in a conference paper, cited as reference [7], on a
different corpus and under a single random split. The present manuscript reuses
those architectures unchanged and serves as their provenance record; it shares
no results, no corpus, no protocol and no text with that paper. Everything
reported here — the audit protocol, the temporal evaluation, the calibration,
the cost measurements and the external validation — is new.

**Principal findings.** A random split saturates the nine-class task, leaving
eleven model pairs statistically indistinguishable and the leaderboard
uninterpretable. A timestamp-only probe survives a label-aware per-class
temporal split at 98.6% accuracy against a 19.4% majority rate, so
chronological evaluation alone does not remove a schedule shortcut; on the
second corpus the same probe falls to 10.3%, which makes the sufficiency of
temporal splitting a property to measure rather than to assume. Under temporal
evaluation the ranking inverts, and logistic regression trails the best macro-F1
by 0.0020 at 1 097 times its throughput.

**Compliance and declarations.** The manuscript is 47 pages and 3.8 MB, within
the journal's limits, formatted single-column, with a 250-word abstract that
carries no undefined acronym and six keywords. The title page and the
anonymised manuscript are uploaded as separate files for double anonymised
review; highlights and vector artwork accompany them. The code repository and
the data archive are withheld from the anonymised manuscript because their
addresses identify the authors, and we will supply both to the editorial office
on request and restore the citations on acceptance.

The work is original, has not been published elsewhere, and is not under
consideration by another journal. All authors have approved the submission. The
authors declare no competing financial or personal interests, and the research
received no specific grant from any funding agency. A generative AI assistant
was used to draft and revise portions of the manuscript text and to review the
analysis code; the authors reviewed and edited all content and take full
responsibility for it, as declared in the manuscript and in the submission
system.

Thank you for considering our work.

Yours sincerely,

Mohamed Ala Eddine Bahri, on behalf of Farah Jemili and Mohamed Mosbah
