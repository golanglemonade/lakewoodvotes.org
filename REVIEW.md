# Open questions to check before launch

Collected from the research pass on 2026-10-09. Candidate lists, measure letters, judges and key dates were cross-checked against the Jefferson County all-inclusive sample ballot (dated 2026-09-30) and Jeffco's On the Ballot page; no corrections were needed. The Colorado Secretary of State site could not be reached from the build environment, so the state's certified list has not been compared directly.

## Federal and statewide offices (`data/2026/federal_statewide.json`)

- [ ] The Colorado Secretary of State's certified 2026 general-election candidate list (sos.state.co.us / coloradosos.gov) could not be loaded from this research environment. Candidate names, parties, and ballot order come from Jefferson County's official 2026 General Election sample ballot and its On the Ballot page, which cross-check with CPR's guide. Compare against the SOS list before publishing.
- [ ] ballot_order is the order on Jefferson County's sample ballot. Colorado sets ballot order by party lottery, so this should match every Lakewood ballot, but check it.
- [ ] Write-in candidates are not listed. The sample ballot shows only a blank write-in line. The Green Papers names declared write-ins for U.S. Senate (Ryan Apelbaum, Will Powers, Donald 'Don' Willoughby), but this is not an official source. Check the SOS list for certified write-ins.
- [ ] RTD: no 2026 RTD director race appears to cover Lakewood. District M (Lakewood) and District D (southeast Lakewood) are not up until 2028, and the RTD descriptions of District N (unincorporated Jefferson County, Evergreen, Conifer, Morrison, Ken-Caryl) and District L do not mention Lakewood. Neither RTD nor the county gave a precinct-level map that could rule out a small piece of Lakewood falling in District N or L. Check against RTD's interactive district map or Jeffco's ballot-style list. The District N race (Cindy Arcuri, appointed incumbent, unopposed) and the District L race (Ian Harwick, incumbent, unopposed) were left out of contests for this reason.
- [ ] Lakewood is listed entirely in CD-7 based on Wikipedia's list of the district's communities. No official map was fetched; confirm with the Colorado redistricting commission map or Jeffco ballot styles.
- [ ] Lt. Gov. Dianne Primavera is not on the ballot. The Green Papers says she is not seeking re-election; no official source was found.
- [ ] Candidate campaign websites are not included (all set to null) and still need to be gathered and checked.

## Statewide ballot measures (`data/2026/state_measures.json`)

- [ ] Amendment 87 passing threshold: the Blue Book, Colorado Newsline and Chalkbeat say a simple majority (Newsline says this is because its constitutional part only repeals language), but a Ballotpedia News article (Sept. 14, 2026) says 55%. This file follows the official Blue Book. Recheck if Ballotpedia corrects its article.
- [ ] Proposition NN fiscal estimates: the Blue Book summary says the state could keep up to $4.6 billion in the first year but is expected to keep about $500 million, while its fiscal section estimates $329.9 million (2026-27) and $521.0 million (2027-28). This file uses the fiscal-section figures; reconcile against the printed Blue Book.
- [ ] The Secretary of State's committee list says it is not final. Committee names are listed as they appear there. They were not checked against TRACER filings or fundraising totals.
- [ ] Some groups on the SOS list (for example Brighter Colorado, People for a Fair Colorado, Vote Common Sense) take positions on many measures. News outlets also name Advance Colorado as the sponsor of several initiatives and Protect Kids Colorado as the sponsor of Propositions 133-135, but those exact names were not cross-checked in TRACER.
- [ ] Ballotpedia's main 'Colorado 2026 ballot measures' page came back with stale content (dated September 2025) and was not cited. The count of 14 was confirmed by the SOS release, the Blue Book, Ballotpedia News, and Colorado Newsline.
- [ ] Whether Ballot Issue 7A (Front Range Passenger Rail District) appears on Lakewood ballots was not checked; that belongs in the local/district section.

## Colorado General Assembly (`data/2026/legislature.json`)

- [ ] No official source found that says which neighborhoods of Lakewood fall in each district (for example north vs. south). who_votes uses population counts and neighboring communities from the redistricting commission instead. Readers should use leg.colorado.gov/findmylegislator; the commission's interactive map could be used to add street-level descriptions.
- [ ] Lakewood resident counts per district are 2020 Census figures from the commission's city-split reports (House: HD23 47,525; HD28 28,468; HD30 80,540. Senate: SD20 66,876; SD22 89,657; both total 156,533).
- [ ] The guide gives no reason the SD20 and SD22 incumbents are leaving. Wikipedia (not cited) says Lisa Cutter is running for Jefferson County Commissioner and Jessie Danielson is term-limited; neither was confirmed from an official source.
- [ ] Not confirmed whether HD28 candidate David Rein is the same person as Lakewood City Council member David Rein (Ward 4).
- [ ] Ballot order was read from the SOS ballot-order table as Democratic/Republican/Libertarian position columns (SD20 and SD22: Republican 1, Democratic 2; HD23: Democratic 1, Libertarian 2; HD28: Democratic 1; HD30: Democratic 1, Republican 2). Worth checking against the Jeffco sample ballot.
- [ ] No campaign websites found for Mancuso, Lieder, Harkess, Duran, Hoffkling, Metler or Rein. Hoffkling has an ActBlue donation page through a third-party group, but no campaign website. Stewart's site comes from her campaign's Linktree page, and Switzer's from GoodParty.org; neither site was opened directly.
- [ ] The SOS list shows no certified write-in candidates for these five races.

## Jefferson County offices and judges (`data/2026/county_judicial.json`)

- [ ] Colorado SOS certified candidate list and Ballotpedia could not be fetched (blocked); candidate lists rely on the Jefferson County official sample ballot (dated 2026-09-30) and the county 'On the Ballot' page.
- [ ] Sheriff: Weston Imer won the June 2026 Republican primary (per The Critical Report), but Randall Doizaki is the Republican on the sample ballot. How and when Doizaki replaced Imer (e.g., vacancy committee) was not confirmed.
- [ ] Treasurer: Bob (Robert) Szulczewski reportedly won the Republican primary, but no Republican is on the official sample ballot. Murl Hendrickson is listed as Libertarian on the county ballot, though the Jeffco GOP candidate page and The Ballot Brief list him with Republicans. The withdrawal and party label should be confirmed with the Clerk; the official ballot label (Libertarian) is used here.
- [ ] Coroner: The Ballot Brief said no Republican was found as of Sept. 8, but the official sample ballot lists Allison Harmon (Republican). The official ballot is used here.
- [ ] Whether Treasurer DiTullio, Assessor Kersgaard, Clerk Gonzalez, or Coroner Cannon are term-limited (versus simply not running) was not confirmed. DiTullio's and Kersgaard's reasons for not running were not checked against an official or news source beyond The Ballot Brief.
- [ ] Robert Hennessy is called the incumbent surveyor only by The Critical Report and The Ballot Brief; not confirmed on a county page.
- [ ] Alexis King's 2024 re-election (term through early 2029) was not confirmed from a fetched source; only her 2020 election was confirmed. The 2026 sample ballot shows no DA race.
- [ ] Which parts of Lakewood lie in Commissioner District 3 was not checked (not needed for voting, since all county voters vote on the seat).
- [ ] Ballot order numbers reflect the order on the county sample ballot as read; confirm against the printed ballot.
- [ ] Candidate websites were not collected (set to null).

## Local measures and how to vote (`data/2026/local_and_voting.json`)

- [ ] Lakewood 2G: no registered issue committee for or against was found. The only named supporters and opponents are council members based on their referral votes and comments.
- [ ] Jeffco 5A/5B and West Metro 7C: the county tax notice has unsigned comments for and against. No named campaign committees were found in sources.
- [ ] West Metro Fire 7C: the district says it serves the City of Lakewood, but not checked against a boundary map whether every Lakewood address is inside the district. Some south Lakewood areas may differ. Voters should check their sample ballot.
- [ ] Front Range Passenger Rail 7A: the $295M/yr and $580M debt figures come from news reports and the county's ballot-title excerpt. The official TABOR notice for 7A was not in the county booklet retrieved.
- [ ] Lakewood 2024 Ballot Issue 2A (permanent TABOR retention): the only source found for 'approved' is a local Substack newsletter. Official 2024 vote totals (Jeffco Clarity results) could not be fetched.
- [ ] Mail ballot send date: Jeffco says Oct. 5; the City of Lakewood page says 'first week of October.' Treated Oct. 5 as the county's date.
- [ ] Charter amendment ballot positions: the mapping (2H = Amendment No. 2 term start; 2J = Amendment No. 1 initiative timing) is from matching titles in the county list against ordinance titles, not from a single official cross-reference.
- [ ] Foothills Park & Recreation District, RTD, Jefferson County government, library district, and Lakewood-area metro districts: no measures found on the county's 2026 local list. Some small metro districts may run separate elections not listed there.
- [ ] Charter amendment numbering (No. 1 / No. 2) for 2H and 2J not shown in county title excerpts; removed from labels.

## Not collected yet

- [ ] Candidate campaign websites (almost all `website` fields are null).
- [ ] Candidate questionnaires / forum answers (the Boulder Votes evidence-graph features).
- [ ] Campaign finance (state TRACER for state/county races and measures).

## Past elections (`data/archive/`)

- [ ] 2023 Jeffco school board counts come from Ballotpedia; check against the county canvass (page 83+ of the PDF wasn't readable).
- [ ] 2023: confirm no Jeffco Schools / county / special-district measure on Lakewood ballots. Ward 5 special election (Jan 30, 2024) not yet added.
- [ ] 2024: statewide totals from Ballotpedia/Wikipedia, not the SOS abstract. Lakewood 2A result read from the county report (copy posted by Town of Morrison).
- [ ] 2025: council counts from the county Statement of Votes Cast run 11/20/2025 (before the canvass); school board counts preliminary; Jeffco totals for Props LL/MM missing.
- [ ] April 2026: turnout percentage not published; campaign-money figures disagree between sources (not shown on the site).

## Candidate research (`data/people/`)

### U.S. House District 7 candidates

- [ ] FEC: api.open.fec.gov and the fec.gov district search page (/data/candidates/house/?state=CO&district=07...) were blocked (proxy policy / robots), and fec.gov later rate-limited us (HTTP 429). FEC figures above come from individual fec.gov candidate/committee pages. FEC filing status for Susan Hall, Lawrence Kyle Clark and Dan "Kilo" Sallis could NOT be checked; do not state they have no filings until someone checks https://www.fec.gov/data/elections/house/CO/07/2026/ in a browser.
- [ ] FEC report names: the fetched fec.gov pages showed coverage through 2026-06-30 but not the report name; that coverage end matches the July Quarterly. The October Quarterly (through Sept 30) is due Oct 15 and the Pre-General Oct 22; refresh all FEC figures after those dates.
- [ ] Questionnaires: CPR News's 2026 CD7 candidate pages are written as CPR summaries of interviews with some short direct quotes, not candidates' written answers, so they are not used as answers. KRDO's profiles (Bennett June 19, Pettersen June 24, 2026) present first-person answers, but the page does not say the candidates submitted them in writing; confirm this if the site needs to. Our fetch tool limits quotes to about 125 characters, so the KRDO answers are trimmed with an ellipsis. An editor could add longer excerpts from the pages.
- [ ] No 2026 CD7 questionnaire was found from Vote411/LWV, the Colorado Sun, the Denver Post, Colorado Community Media or Colorado Newsline (Colorado Newsline's CD7 guide page https://coloradonewsline.com/voter-guides/contests/2026-general-u-s-house-7th-district/ failed to load). Check again closer to ballot mailing.
- [ ] Ballotpedia: Joe Krzeczkowski has Candidate Connection answers (key messages on a 'two-tiered justice system', an 'Economy of Abundance' and overturning Citizens United), but the question text did not appear in our fetch, so they are not included. iVoterGuide says Lawrence Kyle Clark completed Ballotpedia's survey, but Ballotpedia blocked our fetches of his page and of Sallis's. Ballotpedia's CD7 race page was a stale pre-primary cache in our fetch.
- [ ] No endorsements were found for Bennett (his site has no endorsements page), Hall, Clark, Sallis or Krzeczkowski. Krzeczkowski's site shows testimonials from private individuals only. Checks of Republican-aligned groups (NRA-PVF, Club for Growth, U.S. Chamber) did not surface any CD7 2026 endorsement; these groups' lists were not fetched directly.
- [ ] Susan Hall website: Politics1 lists https://susanhallforcongress.com/, but the site blocked our fetch, and CPR says 'No campaign materials were found at press time.' Politics1 also describes her as a teacher and peace activist who ran in 2012 and 2024. The office she ran for was not verified.
- [ ] Krzeczkowski: Politics1 lists votejoek.com as his website, while CPR and the campaign use joeforco.com. Politics1 describes Sallis as a 2010 gubernatorial candidate; this was not verified elsewhere, so it is not in the bio. Sallis's site says he has called the district home since 1967.
- [ ] Lawrence Kyle Clark: no campaign website or questionnaire answers were found. iVoterGuide shows 'Did not answer' on every question.

### Jefferson County candidates

- [ ] Sheriff: Weston Imer won the June 30 Republican primary (src-critical-report-primaries), but Randall Doizaki is the Republican on the county's general-election candidate list (src-jeffco-on-the-ballot). No source found explaining the switch (withdrawal + vacancy committee is the usual Colorado mechanism, but not confirmed). Imer's campaign site still calls him the 'Republican Nominee' (src-imer-site) and GoodParty.org still lists him (src-goodparty-imer). Doizaki told a Sept. 14 GOP event 'I'm running because I was asked to' (src-ctr-marx-event). Confirm with the Clerk's Elections Division (303-271-8111).
- [ ] Treasurer: Bob (Robert) Szulczewski was the Republican primary nominee (src-critical-report-primaries); GoodParty.org still lists him as a Republican candidate (src-goodparty-szulczewski), but no Republican is on the county list (src-jeffco-on-the-ballot). No source found on a withdrawal or why no vacancy replacement appears. Hendrickson's Libertarian Party profile says no Republican is running (src-lp-hendrickson). The Jefferson County Republican Party lists Libertarian Murl Hendrickson as its Treasurer candidate on its 'Meet Your 2026 Candidates' page without an explicit endorsement label (src-jeffco-gop-candidates); not recorded as an endorsement.
- [ ] Campaign finance: TRACER candidate search is a form-postback page that could not be queried through the available tools (src-tracer-search); direct downloads to tracer.sos.colorado.gov (bulk data) were blocked by the network proxy. Only Marinelli's candidate-detail page was reachable via a direct link. Finance for the other 13 candidates is missing; the Oct. 13, 2026 reports will also be new.
- [ ] Questionnaires: no published written Q&A from the approved outlets (Vote411/LWV Jefferson County, CPR, Colorado Sun, Colorado Community Media, Denver Gazette, Denver Post, Ballotpedia) was found for these county races. Ballotpedia and Colorado Community Media pages returned robots-disallowed; Vote411 requires an address lookup; lwvjeffco.org failed to load. LWV Jefferson County held a county-candidate forum on Oct. 1 (per goldenunited.org; not a written questionnaire). Arvadans For Progressive Action (an advocacy group) published survey answers from Cutter, Hensel, Proctor, Kerr, Ketcham and Lobello (src-apa-2026-guide), not used because it is not on the approved outlet list.
- [ ] Cutter's 'Jeffco Endorsements' page shows endorsers only as images (filenames suggest Neguse, Zenzinger, Kerr, Bridges, Kolker, Titone, Duran, Stewart, Proctor, others) (src-cutter-jeffco-endorsements); not recorded. Her site's 'Organizations' page appears to be a legacy Senate list and was not used.
- [ ] Kerr's campaign site shows three unlabeled logos (filenames suggest IBEW, CWF, DALF) (src-kerr-home); only DALF is recorded, from DALF's own page.
- [ ] Endorsement lists for Kerr, Hensel and Lobello were read through a page-summarizing fetch; spellings should be spot-checked (e.g., Hensel's page reportedly prints 'Brittney Pettersen' and 'Claire Carmelia'; Lobello's page reportedly prints 'Westminister Mayor' with 'Claire Camelia', omitted here pending verification).
- [ ] Eric Proctor's campaign site (ericproctor.com) blocks automated fetching; website taken from the Jeffco Democrats candidate page. His bio relies partly on his own answers published by Arvadans For Progressive Action.
- [ ] Paul Poston's site (paulforclerk.com) returned no readable content; no bio beyond nominee status. Vera King has no campaign website found; her bio relies on The Critical Report's one-word description.
- [ ] Robert Hennessy: incumbency and employer come from BallotReady, not a county biography; the county Leadership page confirms he is the current Surveyor.
- [ ] Allison Harmon: what happens if she wins without the required certification is unresolved (src-cbs-harmon). No campaign website found.
- [ ] No sheriff endorsements found from FOP, Jeffco deputies associations or other law-enforcement groups for either Marinelli or Doizaki; Marinelli's campaign site lists no endorsements and Doizaki's site has only individual testimonials. No newspaper editorial endorsements found for any of these county races as of Oct. 9.

### Colorado legislature candidates

- [ ] TRACER: WebFetch works on TRACER pages, but the Candidate Search form is a postback that can't be driven by URL, and direct HTTP access to tracer.sos.colorado.gov is blocked from this environment. Candidate detail pages were found only for Lieder, Rein and Stewart. Mancuso, Harkess, Duran, Hoffkling, Metler and Switzer figures come from TRACER's Quick Stats PDFs (contributions/expenditures only, no cash on hand or report period). Their committee names come from campaign-site disclaimers and should be checked on TRACER.
- [ ] TRACER Quick Stats PDFs were inconsistent: rpt_QuickStatsMapDetail_1.pdf (Senate, footer 9/21/2026) and _2.pdf (Senate, footer 9/22/2026) show different Senate totals. The 9/22 figures are used. The Lieder candidate detail page (Sept 8 report) may be stale, because TRACER listed later filings for other candidates. Re-check all totals after the Oct. 19 reports.
- [ ] Questionnaires: no written Q&A for any of these 9 candidates was found in the 2026 CPR News guide (statewide/federal races only), the Colorado Sun (robots-blocked), Colorado Community Media (no 2026 profiles found), Colorado Politics (its primary roundup skipped SD20/SD22) or Ballotpedia (2026 pages not fetchable or showing 'not completed'). Vote411 answers are rendered client-side and weren't readable. LWV Jefferson County held recorded forums for HD23 (Hoffkling, Metler) and HD30 (Stewart, Switzer), but those are video, not written answers. RMEQ Action Fund published Hoffkling's written answers, but those were not quoted because the source is an endorsing group and the full verbatim text wasn't captured.
- [ ] David Rein: the TRACER filing (David L. Rein Jr., Democratic, HD28), the campaign 'Meet Dave' page (Lakewood City Council, 40 West Arts board, six years on the Lakewood Advisory Commission, lawyer) and the City of Lakewood Ward 4 page (lawyer, 40 West Arts, six years on the Lakewood Advisory Commission) match. They are treated as the same person. If elected, he would leave a council term that runs to November 2027; vacancy handling is not covered here.
- [ ] One Colorado's endorsement page labels Alexis Hoffkling as 'SD-23'. She is recorded as endorsed for HD-23 on the assumption that this is a typo. The page also marks Dave Rein as an incumbent, which is inaccurate for HD-28.
- [ ] Colorado WINS 'Our Endorsements' page has no explicit year. It is treated as 2026 because it lists Monica Duran for Senate District 22 and Hoffkling/Rein for their 2026 House seats.
- [ ] The SEIU endorsements come from SEIU Local 105's 2026 voter guide page, headed as SEIU Colorado endorsements. It may be worth checking which SEIU entity is the endorser of record.
- [ ] Not confirmed: LPAC lists Hoffkling among 'Our Candidates' without the word 'endorse'. Pages that failed to load: the Hoffkling campaign endorsements page (robots-blocked), the Rein campaign endorsements page (fetch error), the UFCW Local 7 full PDF (fetch error; only Lieder was visible on the HTML page), the Sierra Club Colorado and RMGO endorsement pages (fetch errors), and the Jeffco Dems Senate page (robots-blocked). No endorsements were found for Mancuso, Harkess, Metler or Switzer. The Colorado Realtors, FOP, Colorado Concern, AFP, NRA and Working Families Party slates were not found.
- [ ] Duran's campaign endorsement list has no date. Its meta description also mentions Plumbers Local 3, The Herod Leadership Fund and Speaker Crisanta Duran, but these are not in the visible list and were not recorded.
- [ ] Mancuso: a talk-show guest profile (kimmonson.com, partly auto-generated) says he was the 2006 Republican nominee against Mark Udall for Congress and later ran for Colorado GOP chair. His campaign site doesn't mention this, so it is left out of the bio pending confirmation.
- [ ] Harkess and Switzer: no job or residence for Harkess was found on his campaign site. Switzer's employer isn't named on his campaign site. A talk-show profile says he works in the music industry and as a startup consultant, but it is unverified.
- [ ] Lieder's campaign site (liederforcolorado.com) appears to contain older House-race content. It is listed as her website because TRACER and Colorado Informed point to it. Stewart's site (rebekahforcolorado.com) still describes her as a Lakewood City Councilor, which is also older content.
- [ ] Colorado WINS's endorsement page lists Sheila Lieder under 'State Senate District 28', apparently a typo for SD 20 (she is running in SD 20).

- [ ] Refresh campaign money after the Oct. 13/15/19/22 filings (TRACER and FEC).
- [ ] TRACER and FEC searches were blocked from the build environment; Hall, Clark and Sallis (CD-7) FEC status and most county candidates' TRACER filings still need to be pulled in a browser.

### Statewide and federal candidate bios

- [ ] Blake Huber identity (answer: yes, same person, confirmed): the Libertarian Party of Colorado's 2026 'Blake Huber for U.S. Senate' candidate sheet (src-lp-huber) says he ran on the Approval Voting Party ticket for vice president in 2016, for Colorado secretary of state in 2018, and for president in 2020 and 2024. Wikipedia's Approval Voting Party article (src-wiki-avp) gives the 2024 ticket as Huber / Andrea Denault (2,196 Colorado votes). Ballotpedia (src-bp-huber) confirms the 2016/2018/2020/2024 runs but does not name Denault. The 2024 run is added to his bio. Note the candidate sheet does not name which state party he chaired.
- [ ] T.J. Cole identity (answer: same person, but the premise is wrong on party): the 2024 CU Regent at-large candidate T.J. Cole ran as the UNITY Party candidate, not Libertarian. CPR's 2024 voter guide (src-cpr-regent-2024) describes Tijani 'TJ' Cole (Unity) as an attorney and former judge on the Wheat Ridge Municipal Court and Boulder District Court who founded Denver Justice High School - the same details as the 2026 Peckman/Cole campaign site (src-peckman-site). Chaffee County election history (src-chaffee-cole) lists T.J. Cole (U) in the 2024 CU Regent at-large and 2022 U.S. Senate general elections. Both runs are added to his bio. I found no Libertarian T.J. Cole in 2024.
- [ ] Adam Withrow: Ballotpedia (src-bp-withrow) and CPR 2024 cover an Adam Withrow (Unity, educator) who ran in CD-3 in 2024. His 2026 Senate site (src-withrow-site) carries the page metadata name 'Adam Withrow for CD3', suggesting the same person, but no source states it outright, so the 2024 run and occupation are left out of the bio.
- [ ] Christopher Baum: CPR's 2024 CD-8 guide (src-cpr-cd8-2024) profiles a Chris Baum (Approval Voting; 20-year Navy veteran, network administrator, owns an interior decorating shop). The 2026 profile (src-bb-baum, citing Election2026.net) calls him a computer consultant and Navy veteran - consistent, but no source links the two explicitly, so the 2024 run is not in the bio. No campaign website found. Bio rests on a secondary aggregator (The Ballot Brief).
- [ ] Stephen T. Hamilton: no occupation, home city or campaign website found (BallotReady lists only Facebook/Instagram). Bio is limited to party nomination and running mate.
- [ ] James K Treibert: earlier candidacies come from BallotReady's profile only; party labels for those races and his occupation/home city were not confirmed.
- [ ] No campaign websites found for Christopher Baum, Blake Huber (The Ballot Brief: none as of Sept. 8, 2026), Stephen T. Hamilton / James K Treibert, Frank Atwood, George Markert or Taralyn Romero. The campaign sites for Marx and Lopez that I fetched did not mention their running mates, so Markert's and Romero's website fields are null. Weiser's site links to a 'Meet Lesley' page, so it is used for Dahlkemper.
- [ ] Eric Mulder was first listed by the Libertarian Party of Colorado as a CU Regent District 6 candidate and Joshua Rodriguez was its earlier governor candidate (src-lp-cands); the July 2026 press release names Mulder as the governor nominee. How the substitution happened was not researched.
- [ ] The Colorado Sun's Aug. 26, 2026 story on third-party candidates could not be fetched (robots/proxy block), so it was not used.
- [ ] Mark Baisley's Woodland Park residence comes from Colorado Politics; the legislature page lists only his counties. His Colorado House years were not confirmed.
- [ ] Amanda Gonzalez: no official Jefferson County bio page found; 'won in 2022' per Colorado Sun (took office Jan 2023 presumably); home city not sourced (Sun says Jefferson County resident).
- [ ] James Wiley: current home city not sourced (campaign mailing address is Littleton; raised partly in Pueblo). Bio relies partly on self-reported KRDO questionnaire and campaign site.
- [ ] Amanda Campbell: campaign site campbellgoodforcolorado.com has no year references and may be a carry-over from 2018/2022 runs; BallotReady lists it for 2026. No 2026 news coverage found (Colorado Politics' SoS roundup omits her). Home city unknown.
- [ ] Celeste Landry: Ballotpedia also lists Melissa Richards (Unaffiliated) in the SoS general election; she is not in our contest list - confirm against certified ballot.
- [ ] Jeff Bridges: Colorado Politics and his campaign call him Joint Budget Committee chair; leg.colorado.gov lists him as JBC vice chair. Bio says 'serves on' the JBC to avoid the conflict.
- [ ] Jodie Barr: no campaign website, home city, or detailed bio found; bio rests only on Colorado Politics.
- [ ] Marilee Langner Sturgis: no bio, home city or campaign website found (GoodParty profile unclaimed; Ballot Brief says no campaign website as of Sept 8, 2026); bio left null. Did not respond to Colorado Politics questionnaire.
- [ ] Michael J. Allen and Jena Griswold: current home cities not sourced.
- [ ] Karla Esser: campaign site karlaesser.com is cited by The Ballot Brief but blocked from direct fetch (robots); not independently verified.
- [ ] Steve Barton: home city not stated (Fremont County GOP chair role suggests Fremont County). iVoterGuide data is self-reported.
- [ ] Ross Klopf: no campaign website (only Facebook 'Ross Klopf for CD7' and X accounts per iVoterGuide); home city unknown. iVoterGuide also shows a 2022 US House CD7 profile, not confirmed elsewhere so omitted from bio.
- [ ] Nolbert Chavez: chavezforcu.com cited by The Ballot Brief but blocked from direct fetch; regents.cu.edu lists an older title (Chief Strategy Officer) while CU Denver's CityCenter page lists Chief of External Initiatives & Executive Director - used the latter.
- [ ] BetteRose Ryan: no campaign website or home city found; LP Colorado spells her name 'BettyRose' in one listing and iVoterGuide uses 'Bette Rose'. Bio is from self-reported iVoterGuide profile.
- [ ] Ballotpedia lists a Melissa Richards (Unaffiliated) for Secretary of State; she is not on the Jefferson County sample ballot we checked. Confirm against the SOS certified list.
- [ ] Karla Esser's website (karlaesser.com) couldn't be opened to confirm; Amanda Campbell's site may be left over from an earlier run.
