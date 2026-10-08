# WD storage recovery and production continuation

Observed 2026-10-08T18:04:08.526880+00:00. GitHub `main` is the authority for the plan and stage progress; WD files and process receipts establish execution evidence.

The user requested reboot, bounded temporary cleanup, an additional 20GB for WSL, migration of working data to Google Drive and continuation through the remaining stages. Actual reboot was 16:46:31.5 UTC. Ubuntu's block device grew exactly 21,474,836,480 bytes (20 GiB), from 1,099,511,627,776 to 1,120,986,464,256 bytes. Filesystem readback passed. This is virtual capacity; the separate 8 GiB project tool image was retained unchanged.

Exactly 28 redundant release-download ZIPs, totaling 2,190,984,189 bytes, were removed after local/remote checksum comparison. Original upload ZIPs, manifests, scientific data and failed-attempt evidence remain. The attached cleanup receipt identifies every deleted copy and its retained original.

The destination is `G:\My Drive\LAB_RM\lab-rm-phylogenomics-196`. Copy PID 20704 is still running at this observation. An identified-process continuation controller waits for successful copy, catchup and full source-to-destination SHA256 verification before starting the external Codex session. Full-copy validation and actual new CLI execution have NOT happened yet. Private session logs, active tools and stable locks remain on C:.

DriveFS probes passed Windows and WSL read/write/fsync/replace and Windows byte locking; G-local junction creation failed and replacement with open handles differs from NTFS. G: is streamed/cache backed and does not establish independent physical disk space or cloud-upload durability. Preserve the C recovery tree. A new explicit migration revision is required; do not relocate historical absolute-argument receipts or tools by a naive junction.

The V5 candidate passed 116 isolated checks: 36 producer/resource/native-cache checks, 63 independent-checker checks, 7 adoption guards and 10 CLI role/argument checks. These are synthetic tests with no biological jobs. Actual Drive/WSL interoperability, historical source gate, source adoption and fresh resource gate remain pending.

Scientific state is unchanged: sequence retrieval/validation, host markers and Stage04a alignments are complete and release verified. Stage04 inference is incomplete; original unsupported-memory-option and V3 allocation failure evidence remains. V4 stopped before native launch for insufficient Windows RAM. Stage05 R-M searches, Stage06 real figure and Stage07 final validation remain NOT_RUN.

Resume with all 196 approved assemblies and unchanged sensitivities/options after migration checks and current headroom pass. Keep two threads, native 3 GiB/outer 3.5 GiB AS limits, Windows 4.5 GiB/Linux 4 GiB availability gates. Passing preflight does not prove memory sufficiency. The user will reset usage manually; automatic reset redemption is disabled for this continuation.
