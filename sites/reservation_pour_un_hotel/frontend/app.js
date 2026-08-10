// Logique client JavaScript pour l'interactivité et appels fetch d'API HTTP REST backend en gérant les réponses.

const API_BASE_URL = 'http://127.0.0.1:5000'; // Assurez-vous que c'est l'URL de votre backend Flask

document.addEventListener('DOMContentLoaded', () => {
    loadReservations();

    const reservationForm = document.getElementById('reservationForm');
    reservationForm.addEventListener('submit', handleFormSubmit);
});

async function loadReservations() {
    const reservationsList = document.getElementById('reservationsList');
    reservationsList.innerHTML = `<tr><td colspan="5" class="py-4 px-4 text-center text-gray-400">Chargement des réservations...</td></tr>`;

    try {
        const response = await fetch(`${API_BASE_URL}/reservations`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const reservations = await response.json();
        
        displayReservations(reservations);

    } catch (error) {
        console.error("Erreur lors du chargement des réservations:", error);
        reservationsList.innerHTML = `<tr><td colspan="5" class="py-4 px-4 text-center text-red-400">Impossible de charger les réservations. Veuillez vérifier la console.</td></tr>`;
    }
}

function displayReservations(reservations) {
    const reservationsList = document.getElementById('reservationsList');
    reservationsList.innerHTML = ''; // Clear previous entries

    if (reservations.length === 0) {
        reservationsList.innerHTML = `<tr><td colspan="5" class="py-4 px-4 text-center text-gray-400">Aucune réservation trouvée.</td></tr>`;
        return;
    }

    reservations.forEach((reservation, index) => {
        const row = document.createElement('tr');
        row.className = index % 2 === 0 ? 'table-row-even' : 'table-row-odd';
        row.innerHTML = `
            <td class="py-3 px-4">${reservation.id}</td>
            <td class="py-3 px-4">${reservation.guest_name}</td>
            <td class="py-3 px-4">${reservation.room_type}</td>
            <td class="py-3 px-4">${reservation.check_in_date}</td>
            <td class="py-3 px-4">${reservation.check_out_date}</td>
        `;
        reservationsList.appendChild(row);
    });
}

async function handleFormSubmit(event) {
    event.preventDefault(); // Empêche le rechargement de la page

    const messageDiv = document.getElementById('message');
    messageDiv.innerHTML = ''; // Clear previous messages
    messageDiv.className = 'mt-4 text-center font-semibold';

    const formData = {
        guest_name: document.getElementById('guestName').value,
        email: document.getElementById('email').value,
        room_type: document.getElementById('roomType').value,
        check_in_date: document.getElementById('checkInDate').value,
        check_out_date: document.getElementById('checkOutDate').value,
    };

    // Basic form validation
    for (const key in formData) {
        if (!formData[key]) {
            messageDiv.textContent = `Veuillez remplir le champ "${key.replace('_', ' ')}".`;
            messageDiv.classList.add('text-red-400');
            return;
        }
    }

    // Date validation
    const checkIn = new Date(formData.check_in_date);
    const checkOut = new Date(formData.check_out_date);
    if (checkIn >= checkOut) {
        messageDiv.textContent = "La date de départ doit être postérieure à la date d'arrivée.";
        messageDiv.classList.add('text-red-400');
        return;
    }


    try {
        const response = await fetch(`${API_BASE_URL}/reservations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        const result = await response.json();

        if (response.ok) {
            messageDiv.textContent = result.message || "Réservation effectuée avec succès !";
            messageDiv.classList.add('text-green-400');
            document.getElementById('reservationForm').reset(); // Réinitialise le formulaire
            loadReservations(); // Recharge la liste des réservations
        } else {
            messageDiv.textContent = result.error || "Erreur lors de la réservation.";
            messageDiv.classList.add('text-red-400');
            console.error("Erreur backend:", result);
        }

    } catch (error) {
        console.error("Erreur lors de l'envoi de la réservation:", error);
        messageDiv.textContent = "Une erreur réseau est survenue. Veuillez réessayer.";
        messageDiv.classList.add('text-red-400');
    }
}