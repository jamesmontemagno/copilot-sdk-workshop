package workshop;

import java.util.List;
import java.util.Locale;

enum FactReviewStatus {
    SUPPORTED("supported"),
    CONTRADICTED("contradicted"),
    NOT_FOUND("not found"),
    NOT_CHECKED("not checked");

    private final String label;

    FactReviewStatus(String label) {
        this.label = label;
    }

    static FactReviewStatus fromLabel(String value) {
        String normalized = value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
        for (FactReviewStatus status : values()) {
            if (status.label.equals(normalized)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown fact review status: " + value);
    }

    @Override
    public String toString() {
        return label;
    }
}

record FactReview(
        String fact,
        FactReviewStatus status,
        String evidenceTitle,
        String evidenceUrl,
        String explanation) {
}

record ProposedAddition(
        String fact,
        String sourceTitle,
        String sourceUrl,
        boolean approved) {
    ProposedAddition withApproved(boolean value) {
        return new ProposedAddition(fact, sourceTitle, sourceUrl, value);
    }
}

record ResearchSource(String title, String url) {
}

record ResearchResult(
        List<FactReview> reviews,
        List<ProposedAddition> additions,
        List<ResearchSource> consultedSources,
        boolean completed,
        String failureMessage) {
    ResearchResult {
        reviews = List.copyOf(reviews);
        additions = List.copyOf(additions);
        consultedSources = List.copyOf(consultedSources);
    }
}
