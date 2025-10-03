package com.priyanshu.password;

import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {
    private static final String PREFS_NAME = "AppPrefs";
    private static final String KEY_PIN_SET = "pin_set";
    private static final String KEY_PIN_HASH = "pin_hash";
    private static final String KEY_CARDS = "cards";
    private List<PasswordCard> cardList = new ArrayList<>();
    private LinearLayout container;
    private Gson gson = new Gson();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button lockButton = findViewById(R.id.btn_lock);
        Button manageCardsButton = findViewById(R.id.btn_edit);
        Button resetPinButton = findViewById(R.id.btn_reset);

        lockButton.setOnClickListener(v -> lockApp());
        manageCardsButton.setOnClickListener(v -> showCardManagementMenu());
        resetPinButton.setOnClickListener(v -> resetPin());

        // Load and display
        loadCards();
        container = findViewById(R.id.cards_container);
        if (container != null) {
            for (PasswordCard card : cardList) {
                if (card == null) continue;

                String app = card.appName != null ? card.appName.trim() : "";
                String user = card.username != null ? card.username.trim() : "";
                String pass = card.password != null ? card.password.trim() : "";

                if (!app.isEmpty() && !user.isEmpty() && !pass.isEmpty()) {
                    createCardView(app, user, pass);
                }
            }
        }
    }

    private void showCardManagementMenu() {
        String[] items = {"Add Password", "Edit Password", "Delete Password"};
        int[] icons = {
                android.R.drawable.ic_menu_add,
                android.R.drawable.ic_menu_edit,
                android.R.drawable.ic_menu_delete
        };

        ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, android.R.layout.select_dialog_item, android.R.id.text1, items) {
            @Override
            public View getView(int position, View convertView, ViewGroup parent) {
                View view = super.getView(position, convertView, parent);
                TextView textView = view.findViewById(android.R.id.text1);
                textView.setCompoundDrawablesWithIntrinsicBounds(icons[position], 0, 0, 0);
                textView.setCompoundDrawablePadding(24);
                if (position == 2) {
                    textView.setTextColor(getColor(android.R.color.holo_red_dark));
                } else {
                    textView.setTextColor(getColor(android.R.color.primary_text_dark));
                }
                return view;
            }
        };

        new AlertDialog.Builder(this)
                .setTitle("Card Options")
                .setAdapter(adapter, (dialog, which) -> {
                    switch (which) {
                        case 0:
                            showAddPasswordDialog();
                            break;
                        case 1:
                            Toast.makeText(this, "Edit selected (not implemented yet)", Toast.LENGTH_SHORT).show();
                            break;
                        case 2:
                            if (cardList.isEmpty()) {
                                Toast.makeText(this, "No passwords to delete", Toast.LENGTH_SHORT).show();
                            } else {
                                showDeletePasswordDialog();
                            }
                            break;
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void showAddPasswordDialog() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);

        EditText etAppName = new EditText(this);
        etAppName.setHint("App/Website Name");
        layout.addView(etAppName);

        EditText etUsername = new EditText(this);
        etUsername.setHint("Username/Email");
        layout.addView(etUsername);

        EditText etPassword = new EditText(this);
        etPassword.setHint("Password");
        etPassword.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        layout.addView(etPassword);

        new AlertDialog.Builder(this)
                .setTitle("Add Password")
                .setView(layout)
                .setPositiveButton("Add", (dialog, which) -> {
                    String appName = etAppName.getText().toString().trim();
                    String username = etUsername.getText().toString().trim();
                    String password = etPassword.getText().toString().trim();

                    if (!appName.isEmpty() && !username.isEmpty() && !password.isEmpty()) {
                        addCardAndSave(appName, username, password);
                    } else {
                        showAddPasswordDialog();
                        Toast.makeText(this, "All fields required", Toast.LENGTH_SHORT).show();
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void createCardView(String appName, String username, String password) {
        CardView cardView = new CardView(this);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, 0, 0, 24);
        cardView.setLayoutParams(params);
        cardView.setRadius(16f);
        cardView.setCardElevation(8f);
        cardView.setUseCompatPadding(true);

        LinearLayout innerLayout = new LinearLayout(this);
        innerLayout.setOrientation(LinearLayout.VERTICAL);
        innerLayout.setPadding(32, 32, 32, 32);

        TextView tvAppName = new TextView(this);
        tvAppName.setText(appName);
        tvAppName.setTextSize(18);
        tvAppName.setTypeface(null, Typeface.BOLD);
        innerLayout.addView(tvAppName);

        TextView tvUsername = new TextView(this);
        tvUsername.setText("Username: " + username);
        innerLayout.addView(tvUsername);

        TextView tvPassword = new TextView(this);
        tvPassword.setText("Password: " + password);
        innerLayout.addView(tvPassword);

        cardView.addView(innerLayout);

        LinearLayout container = findViewById(R.id.cards_container);
        if (container != null) {
            container.addView(cardView);
        }
    }

    private void addCardAndSave(String appName, String username, String password) {
        createCardView(appName, username, password);
        PasswordCard newCard = new PasswordCard(appName, username, password);
        cardList.add(newCard);
        saveCards();
    }

    private void saveCards() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        SharedPreferences.Editor editor = prefs.edit();
        String json = gson.toJson(cardList);
        editor.putString(KEY_CARDS, json);
        editor.apply();
    }

    private void loadCards() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String json = prefs.getString(KEY_CARDS, null);
        cardList = new ArrayList<>();

        if (json != null && !json.trim().isEmpty()) {
            try {
                Type type = new TypeToken<ArrayList<PasswordCard>>() {}.getType();
                List<PasswordCard> loaded = gson.fromJson(json, type);
                if (loaded != null) {
                    for (PasswordCard card : loaded) {
                        if (card != null) {
                            cardList.add(card);
                        }
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    private void lockApp() {
        Intent intent = new Intent(this, Lockscreen.class);
        startActivity(intent);
        finish();
    }

    private void resetPin() {
        new AlertDialog.Builder(this)
                .setTitle("Reset PIN")
                .setMessage("Are you sure you want to reset your PIN?")
                .setPositiveButton("Yes, Reset", (dialog, which) -> {
                    SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
                    prefs.edit()
                            .remove(KEY_PIN_HASH)
                            .putBoolean(KEY_PIN_SET, false)
                            .apply();

                    lockApp();
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void showDeletePasswordDialog() {
        List<String> appNames = new ArrayList<>();
        for (PasswordCard card : cardList) {
            appNames.add(card.appName != null ? card.appName : "Unknown");
        }

        new AlertDialog.Builder(this)
                .setTitle("Delete Password")
                .setItems(appNames.toArray(new String[0]), (dialog, which) -> {
                    String appName = appNames.get(which);
                    new AlertDialog.Builder(this)
                            .setTitle("Confirm Delete")
                            .setMessage("Delete password for \"" + appName + "\"?")
                            .setPositiveButton("Delete", (confirmDialog, i) -> {
                                cardList.remove(which);
                                saveCards();
                                refreshCardViews();
                                Toast.makeText(this, "Password deleted", Toast.LENGTH_SHORT).show();
                            })
                            .setNegativeButton("Cancel", null)
                            .show();
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void refreshCardViews() {
        container.removeAllViews();
        for (PasswordCard card : cardList) {
            if (card == null) continue;
            String app = card.appName != null ? card.appName.trim() : "";
            String user = card.username != null ? card.username.trim() : "";
            String pass = card.password != null ? card.password.trim() : "";
            if (!app.isEmpty() && !user.isEmpty() && !pass.isEmpty()) {
                createCardView(app, user, pass);
            }
        }
    }
}