package workshop;

public record TitleValidation(long titleCount) {
    public boolean present() {
        return titleCount == 1;
    }

    public boolean valid() {
        return present();
    }
}
